package services

import (
	"bytes"
	"ecommerce-dispute-platform/config"
	"ecommerce-dispute-platform/database"
	"ecommerce-dispute-platform/models"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

var (
	ErrAnalysisRequestNotFound  = errors.New("analysis request not found")
	ErrRequestIDMismatch        = errors.New("request ID mismatch")
	ErrTicketIDMismatch         = errors.New("ticket ID mismatch")
	ErrAnalysisAlreadyCompleted = errors.New("analysis already completed")
	ErrEvidenceNotFound         = errors.New("evidence not found")
)

type AnalysisService struct {
	MLServiceURL string
	CallbackURL  string
}

type AsyncAnalysisRequest struct {
	RequestID    string `json:"request_id"`
	TicketID     uint   `json:"ticket_id"`
	EvidenceID   uint   `json:"evidence_id"`
	AnalysisType string `json:"analysis_type"`
	CallbackURL  string `json:"callback_url"`
}

type AsyncAnalysisResponse struct {
	RequestID   string      `json:"request_id"`
	TicketID    uint        `json:"ticket_id"`
	EvidenceID  uint        `json:"evidence_id"`
	Status      string      `json:"status"`
	Result      interface{} `json:"result,omitempty"`
	Error       string      `json:"error,omitempty"`
	CompletedAt string      `json:"completed_at,omitempty"`
}

type AnalysisCallbackData struct {
	RequestID   string      `json:"request_id"`
	TicketID    uint        `json:"ticket_id"`
	EvidenceID  uint        `json:"evidence_id"`
	Status      string      `json:"status"`
	Result      interface{} `json:"result,omitempty"`
	Error       string      `json:"error,omitempty"`
	CompletedAt string      `json:"completed_at,omitempty"`
}

func NewAnalysisService() *AnalysisService {
	mlURL := "http://localhost:5000"
	if config.AppConfig != nil {
		if config.AppConfig.MLService.URL != "" {
			mlURL = config.AppConfig.MLService.URL
		} else if config.AppConfig.ImageAnalysis.ServiceURL != "" {
			mlURL = config.AppConfig.ImageAnalysis.ServiceURL
		}
	}
	return &AnalysisService{
		MLServiceURL: mlURL,
		CallbackURL:  "http://localhost:8080/api/analysis/callback",
	}
}

func (s *AnalysisService) GenerateRequestID() string {
	return uuid.New().String()
}

func (s *AnalysisService) CreateAnalysisRequest(tx *gorm.DB, ticketID uint, evidenceID uint, analysisType string) (*models.AnalysisRequest, error) {
	requestID := s.GenerateRequestID()

	request := &models.AnalysisRequest{
		RequestID:    requestID,
		TicketID:     ticketID,
		EvidenceID:   evidenceID,
		Status:       "pending",
		AnalysisType: analysisType,
		RequestedAt:  time.Now(),
		CallbackURL:  s.CallbackURL,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	if err := tx.Create(request).Error; err != nil {
		return nil, err
	}

	var evidence models.TicketEvidence
	if err := tx.First(&evidence, evidenceID).Error; err != nil {
		return nil, err
	}
	evidence.AnalysisRequestID = requestID
	evidence.AnalysisStatus = "pending"
	if err := tx.Save(&evidence).Error; err != nil {
		return nil, err
	}

	activity := &models.TicketActivity{
		TicketID:   ticketID,
		Action:     "analysis_requested",
		ActionType: "update",
		Details:    fmt.Sprintf("图像分析请求已创建，RequestID: %s", requestID),
		CreatedAt:  time.Now(),
	}
	if err := tx.Create(activity).Error; err != nil {
		return nil, err
	}

	return request, nil
}

func (s *AnalysisService) SubmitAsyncAnalysis(request *models.AnalysisRequest, imagePath string) error {
	requestID := request.RequestID

	go func() {
		time.Sleep(100 * time.Millisecond)

		result, err := s.callMLService(imagePath, request.AnalysisType)
		if err != nil {
			s.handleAnalysisError(requestID, request.TicketID, request.EvidenceID, err.Error())
			return
		}

		callbackData := &AnalysisCallbackData{
			RequestID:   requestID,
			TicketID:    request.TicketID,
			EvidenceID:  request.EvidenceID,
			Status:      "completed",
			Result:      result,
			CompletedAt: time.Now().Format(time.RFC3339),
		}

		s.processCallback(callbackData)
	}()

	database.DB.Model(&models.AnalysisRequest{}).Where("id = ?", request.ID).Updates(map[string]interface{}{
		"status":    "processing",
		"updated_at": time.Now(),
	})

	return nil
}

func (s *AnalysisService) callMLService(imagePath string, analysisType string) (interface{}, error) {
	file, err := os.Open(imagePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	part, err := writer.CreateFormFile("file", filepath.Base(imagePath))
	if err != nil {
		return nil, err
	}

	_, err = io.Copy(part, file)
	if err != nil {
		return nil, err
	}

	if analysisType != "" {
		writer.WriteField("analysis_type", analysisType)
	}

	writer.Close()

	endpoint := fmt.Sprintf("%s/api/image/analyze", s.MLServiceURL)
	req, err := http.NewRequest("POST", endpoint, body)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result map[string]interface{}
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, err
	}

	return result, nil
}

func (s *AnalysisService) ValidateCallback(callbackData *AnalysisCallbackData) (*models.AnalysisRequest, error) {
	var request models.AnalysisRequest
	if err := database.DB.Where("request_id = ?", callbackData.RequestID).First(&request).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrAnalysisRequestNotFound
		}
		return nil, err
	}

	if request.RequestID != callbackData.RequestID {
		return nil, ErrRequestIDMismatch
	}

	if request.TicketID != callbackData.TicketID {
		return nil, ErrTicketIDMismatch
	}

	if request.Status == "completed" || request.Status == "failed" {
		return nil, ErrAnalysisAlreadyCompleted
	}

	return &request, nil
}

func (s *AnalysisService) ProcessCallback(callbackData *AnalysisCallbackData) error {
	return s.processCallback(callbackData)
}

func (s *AnalysisService) processCallback(callbackData *AnalysisCallbackData) error {
	return database.DB.Transaction(func(tx *gorm.DB) error {
		request, err := s.ValidateCallback(callbackData)
		if err != nil {
			return err
		}

		now := time.Now()
		request.Status = callbackData.Status
		request.CompletedAt = &now
		request.UpdatedAt = now

		if callbackData.Status == "failed" {
			request.ErrorCode = "ANALYSIS_ERROR"
			request.ErrorMessage = callbackData.Error
			request.RetryCount++
		}

		if err := tx.Save(request).Error; err != nil {
			return err
		}

		var evidence models.TicketEvidence
		if err := tx.First(&evidence, request.EvidenceID).Error; err != nil {
			return err
		}

		evidence.AnalysisStatus = callbackData.Status

		if callbackData.Status == "completed" && callbackData.Result != nil {
			evidence.IsAnalyzed = true
			resultJSON, _ := json.Marshal(callbackData.Result)
			evidence.Analysis = string(resultJSON)

			if resultMap, ok := callbackData.Result.(map[string]interface{}); ok {
				if data, ok := resultMap["data"].(map[string]interface{}); ok {
					if score, ok := data["analysis_score"].(float64); ok {
						evidence.AnalysisScore = score
					} else if score, ok := data["quality_score"].(float64); ok {
						evidence.AnalysisScore = score
					}
				}
			}
		}

		if err := tx.Save(&evidence).Error; err != nil {
			return err
		}

		activity := &models.TicketActivity{
			TicketID:  request.TicketID,
			Action:    "analysis_completed",
			ActionType: "update",
			Details:   fmt.Sprintf("图像分析完成，状态: %s, RequestID: %s", callbackData.Status, callbackData.RequestID),
			CreatedAt: time.Now(),
		}
		if err := tx.Create(activity).Error; err != nil {
			return err
		}

		s.createImageAnalysisRecord(tx, request, evidence, callbackData.Result)

		return nil
	})
}

func (s *AnalysisService) createImageAnalysisRecord(tx *gorm.DB, request *models.AnalysisRequest, evidence models.TicketEvidence, result interface{}) {
	if result == nil {
		return
	}

	resultMap, ok := result.(map[string]interface{})
	if !ok {
		return
	}

	data, ok := resultMap["data"].(map[string]interface{})
	if !ok {
		return
	}

	hasIssue := false
	hasFalseClaim := false
	issueType := ""
	falseClaimType := ""
	confidence := 0.0
	description := ""
	textExtracted := ""

	if textAnalysis, ok := data["text_analysis"].(map[string]interface{}); ok {
		if extracted, ok := textAnalysis["extracted_text"].(string); ok {
			textExtracted = extracted
		}
		if hfc, ok := textAnalysis["has_false_claim"].(bool); ok {
			hasFalseClaim = hfc
		}
	}

	if falseAdv, ok := data["false_advertising"].(map[string]interface{}); ok {
		if hfc, ok := falseAdv["has_false_claim"].(bool); ok {
			hasFalseClaim = hasFalseClaim || hfc
		}
		if fct, ok := falseAdv["false_claim_type"].(string); ok {
			falseClaimType = fct
		}
		if conf, ok := falseAdv["confidence"].(float64); ok {
			confidence = conf
		}
	}

	if imageAnalysis, ok := data["image_analysis"].(map[string]interface{}); ok {
		if hi, ok := imageAnalysis["has_issue"].(bool); ok {
			hasIssue = hi
		}
		if it, ok := imageAnalysis["issue_type"].(string); ok {
			issueType = it
		}
		if conf, ok := imageAnalysis["confidence"].(float64); ok {
			if confidence == 0 {
				confidence = conf
			}
		}
		if desc, ok := imageAnalysis["description"].(string); ok {
			description = desc
		}
	}

	imageAnalysis := &models.ImageAnalysis{
		EvidenceID:     evidence.ID,
		AnalysisType:   request.AnalysisType,
		HasIssue:       hasIssue,
		IssueType:      issueType,
		Confidence:     confidence,
		Description:    description,
		TextExtracted:  textExtracted,
		HasFalseClaim:  hasFalseClaim,
		FalseClaimType: falseClaimType,
		CreatedAt:      time.Now(),
	}

	details, _ := json.Marshal(result)
	imageAnalysis.Details = string(details)

	tx.Create(imageAnalysis)
}

func (s *AnalysisService) handleAnalysisError(requestID string, ticketID uint, evidenceID uint, errorMsg string) {
	callbackData := &AnalysisCallbackData{
		RequestID:  requestID,
		TicketID:   ticketID,
		EvidenceID: evidenceID,
		Status:     "failed",
		Error:      errorMsg,
	}
	s.processCallback(callbackData)
}

func (s *AnalysisService) GetAnalysisStatus(requestID string) (*models.AnalysisRequest, error) {
	var request models.AnalysisRequest
	if err := database.DB.Where("request_id = ?", requestID).First(&request).Error; err != nil {
		return nil, err
	}
	return &request, nil
}

func (s *AnalysisService) GetTicketAnalyses(ticketID uint) ([]models.AnalysisRequest, error) {
	var requests []models.AnalysisRequest
	if err := database.DB.Where("ticket_id = ?", ticketID).Order("created_at DESC").Find(&requests).Error; err != nil {
		return nil, err
	}
	return requests, nil
}
