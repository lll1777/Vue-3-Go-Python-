package services

import (
	"ecommerce-dispute-platform/config"
	"ecommerce-dispute-platform/database"
	"ecommerce-dispute-platform/models"
	"encoding/json"
	"errors"
	"fmt"
	"path/filepath"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

var (
	ErrArbitrationLocked   = errors.New("ticket is locked for arbitration")
	ErrFinalDecisionExists = errors.New("final decision already exists")
)

type TicketService struct {
	lockService     *LockService
	analysisService *AnalysisService
}

type AutoDecisionResult struct {
	Decision   string   `json:"decision"`
	Confidence int      `json:"confidence"`
	Reason     string   `json:"reason"`
	Rules      []string `json:"rules"`
}

func NewTicketService() *TicketService {
	return &TicketService{
		lockService:     NewLockService(),
		analysisService: NewAnalysisService(),
	}
}

func (s *TicketService) CreateTicket(ticket *models.Ticket) error {
	ticket.TicketNo = generateTicketNo()
	ticket.Status = "pending"
	ticket.Stage = "evidence"
	ticket.SLAStartTime = time.Now()
	ticket.SLAEndTime = time.Now().Add(time.Duration(config.AppConfig.SLA.EvidenceHours) * time.Hour)
	ticket.SLARemainingHours = config.AppConfig.SLA.EvidenceHours
	ticket.SLAPercentage = 0

	return database.DB.Transaction(func(tx *gorm.DB) error {
		if err := tx.Create(ticket).Error; err != nil {
			return err
		}

		activity := &models.TicketActivity{
			TicketID:   ticket.ID,
			UserID:     ticket.BuyerID,
			Action:     "create_ticket",
			ActionType: "create",
			Details:    "创建维权工单",
			CreatedAt:  time.Now(),
		}
		if err := tx.Create(activity).Error; err != nil {
			return err
		}

		return nil
	})
}

func (s *TicketService) GetTicketByID(id uint) (*models.Ticket, error) {
	var ticket models.Ticket
	err := database.DB.Preload("Buyer").Preload("Seller").Preload("Arbitrator").Preload("Order").
		First(&ticket, id).Error
	if err != nil {
		return nil, err
	}
	return &ticket, nil
}

func (s *TicketService) GetTickets(userID uint, role string, page, pageSize int, filters map[string]interface{}) ([]models.Ticket, int64, error) {
	var tickets []models.Ticket
	var total int64

	query := database.DB.Model(&models.Ticket{}).Preload("Buyer").Preload("Seller")

	if role == "buyer" {
		query = query.Where("buyer_id = ?", userID)
	} else if role == "seller" {
		query = query.Where("seller_id = ?", userID)
	} else if role == "arbitrator" {
		query = query.Where("arbitrator_id = ? OR status IN ?", userID, []string{"arbitration", "platform"})
	}

	if ticketNo, ok := filters["ticket_no"].(string); ok && ticketNo != "" {
		query = query.Where("ticket_no LIKE ?", "%"+ticketNo+"%")
	}
	if orderNo, ok := filters["order_no"].(string); ok && orderNo != "" {
		query = query.Where("order_no LIKE ?", "%"+orderNo+"%")
	}
	if ticketType, ok := filters["type"].(string); ok && ticketType != "" {
		query = query.Where("type = ?", ticketType)
	}
	if status, ok := filters["status"].(string); ok && status != "" {
		query = query.Where("status = ?", status)
	}

	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	offset := (page - 1) * pageSize
	if err := query.Offset(offset).Limit(pageSize).Order("created_at DESC").Find(&tickets).Error; err != nil {
		return nil, 0, err
	}

	return tickets, total, nil
}

func (s *TicketService) UpdateTicketStatus(ticketID uint, newStatus, newStage string, userID uint, reason string) error {
	return database.DB.Transaction(func(tx *gorm.DB) error {
		var ticket models.Ticket
		if err := tx.First(&ticket, ticketID).Error; err != nil {
			return err
		}

		oldStatus := ticket.Status
		ticket.Status = newStatus
		ticket.Stage = newStage

		if newStage != "" {
			s.updateSLATimings(&ticket, newStage)
		}

		if err := tx.Save(&ticket).Error; err != nil {
			return err
		}

		activity := &models.TicketActivity{
			TicketID:   ticketID,
			UserID:     userID,
			Action:     "status_change",
			ActionType: "update",
			Details:    reason,
			FromStatus: oldStatus,
			ToStatus:   newStatus,
			CreatedAt:  time.Now(),
		}
		if err := tx.Create(activity).Error; err != nil {
			return err
		}

		return nil
	})
}

func (s *TicketService) updateSLATimings(ticket *models.Ticket, stage string) {
	config := config.AppConfig.SLA
	var slaHours float64

	switch stage {
	case "evidence":
		slaHours = config.EvidenceHours
	case "negotiation":
		slaHours = config.NegotiationHours
		ticket.NegotiationStartAt = &[]time.Time{time.Now()}[0]
	case "arbitration":
		slaHours = config.ArbitrationHours
		ticket.ArbitrationStartAt = &[]time.Time{time.Now()}[0]
	default:
		slaHours = config.EvidenceHours
	}

	ticket.SLAStartTime = time.Now()
	ticket.SLAEndTime = time.Now().Add(time.Duration(slaHours) * time.Hour)
	ticket.SLARemainingHours = slaHours
	ticket.SLAPercentage = 0
	ticket.SLAWarningSent = false
	ticket.SLACriticalSent = false
}

func (s *TicketService) SubmitEvidence(ticketID uint, evidence *models.TicketEvidence) error {
	return database.DB.Transaction(func(tx *gorm.DB) error {
		if err := tx.Create(evidence).Error; err != nil {
			return err
		}

		var ticket models.Ticket
		if err := tx.First(&ticket, ticketID).Error; err != nil {
			return err
		}

		if ticket.Status == "pending" {
			ticket.Status = "evidence"
			ticket.EvidenceSubmittedAt = &[]time.Time{time.Now()}[0]
			if err := tx.Save(&ticket).Error; err != nil {
				return err
			}
		}

		if evidence.Type == "image" && s.isImageFile(evidence.FileName) {
			request, err := s.analysisService.CreateAnalysisRequest(tx, ticketID, evidence.ID, "all")
			if err != nil {
				fmt.Printf("Warning: failed to create analysis request: %v\n", err)
			} else {
				go func() {
					time.Sleep(500 * time.Millisecond)
					imagePath := "." + evidence.FileURL
					s.analysisService.SubmitAsyncAnalysis(request, imagePath)
				}()
			}
		}

		activity := &models.TicketActivity{
			TicketID:   ticketID,
			UserID:     evidence.UserID,
			Action:     "submit_evidence",
			ActionType: "update",
			Details:    fmt.Sprintf("提交证据: %s", evidence.FileName),
			CreatedAt:  time.Now(),
		}
		if err := tx.Create(activity).Error; err != nil {
			return err
		}

		return nil
	})
}

func (s *TicketService) isImageFile(filename string) bool {
	ext := filepath.Ext(filename)
	imageExts := map[string]bool{
		".jpg":  true,
		".jpeg": true,
		".png":  true,
		".gif":  true,
		".bmp":  true,
		".webp": true,
	}
	return imageExts[ext]
}

func (s *TicketService) AddMessage(ticketID uint, message *models.TicketMessage) error {
	message.TicketID = ticketID
	message.CreatedAt = time.Now()
	return database.DB.Create(message).Error
}

func (s *TicketService) GetMessages(ticketID uint, page, pageSize int) ([]models.TicketMessage, int64, error) {
	var messages []models.TicketMessage
	var total int64

	query := database.DB.Model(&models.TicketMessage{}).Where("ticket_id = ?", ticketID).Preload("User")

	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	offset := (page - 1) * pageSize
	if err := query.Offset(offset).Limit(pageSize).Order("created_at ASC").Find(&messages).Error; err != nil {
		return nil, 0, err
	}

	return messages, total, nil
}

func (s *TicketService) Escalate(ticketID uint, arbitratorID uint, reason string) error {
	return database.DB.Transaction(func(tx *gorm.DB) error {
		var ticket models.Ticket
		if err := tx.First(&ticket, ticketID).Error; err != nil {
			return err
		}

		if ticket.ArbitrationLocked {
			return ErrArbitrationLocked
		}

		if ticket.FinalDecision != nil {
			return ErrFinalDecisionExists
		}

		lockResult, err := s.lockService.AcquireLock(tx, ticketID, arbitratorID, fmt.Sprintf("升级平台仲裁: %s", reason))
		if err != nil {
			return err
		}
		if !lockResult.Success {
			return ErrArbitrationLocked
		}

		ticket.IsEscalated = true
		ticket.EscalatedReason = reason
		ticket.EscalatedAt = &[]time.Time{time.Now()}[0]
		ticket.Status = "platform"
		ticket.Stage = "arbitration"
		ticket.ArbitratorID = &arbitratorID

		s.updateSLATimings(&ticket, "arbitration")

		if err := tx.Save(&ticket).Error; err != nil {
			return err
		}

		activity := &models.TicketActivity{
			TicketID:   ticketID,
			UserID:     arbitratorID,
			Action:     "escalate_and_lock",
			ActionType: "update",
			Details:    fmt.Sprintf("工单已升级到平台仲裁，仲裁锁已获取，自动判责已暂停。原因: %s", reason),
			CreatedAt:  time.Now(),
		}
		if err := tx.Create(activity).Error; err != nil {
			return err
		}

		return nil
	})
}

func (s *TicketService) AutoDecide(ticketID uint) (*AutoDecisionResult, error) {
	canDecide, reason := s.lockService.CanAutoDecide(ticketID)
	if !canDecide {
		return &AutoDecisionResult{
			Decision:   "blocked",
			Confidence: 0,
			Reason:     fmt.Sprintf("自动判责已被阻止: %s", reason),
			Rules:      []string{},
		}, ErrArbitrationLocked
	}

	var ticket models.Ticket
	if err := database.DB.Preload("Seller").First(&ticket, ticketID).Error; err != nil {
		return nil, err
	}

	if ticket.FinalDecision != nil {
		return &AutoDecisionResult{
			Decision:   "blocked",
			Confidence: 0,
			Reason:     "工单已有最终裁决，自动判责被阻止",
			Rules:      []string{},
		}, ErrFinalDecisionExists
	}

	var evidences []models.TicketEvidence
	database.DB.Where("ticket_id = ?", ticketID).Find(&evidences)

	var rules []models.Rule
	database.DB.Where("is_active = ?", true).Order("priority DESC").Find(&rules)

	result := &AutoDecisionResult{
		Decision:   "pending",
		Confidence: 0,
		Reason:     "证据不足，等待更多信息",
		Rules:      []string{},
	}

	weights := 0
	decisionCounts := make(map[string]int)

	for _, rule := range rules {
		match, err := s.evaluateRule(&rule, &ticket, evidences)
		if err != nil {
			continue
		}

		if match {
			result.Rules = append(result.Rules, rule.Name)
			weights += rule.Weight

			var ruleAction map[string]interface{}
			json.Unmarshal([]byte(rule.Actions), &ruleAction)

			if decision, ok := ruleAction["decision"].(string); ok {
				decisionCounts[decision] += rule.Weight
			}
		}
	}

	if len(result.Rules) > 0 {
		maxDecision := ""
		maxWeight := 0
		for decision, weight := range decisionCounts {
			if weight > maxWeight {
				maxWeight = weight
				maxDecision = decision
			}
		}

		if maxDecision != "" {
			result.Decision = maxDecision
			result.Confidence = (maxWeight * 100) / weights
			result.Reason = fmt.Sprintf("匹配到 %d 条规则，置信度 %d%%", len(result.Rules), result.Confidence)

			err := database.DB.Transaction(func(tx *gorm.DB) error {
				var currentTicket models.Ticket
				if err := tx.First(&currentTicket, ticketID).Error; err != nil {
					return err
				}

				if currentTicket.ArbitrationLocked {
					return ErrArbitrationLocked
				}

				if currentTicket.FinalDecision != nil {
					return ErrFinalDecisionExists
				}

				currentTicket.AutoDecision = &maxDecision
				conf := result.Confidence
				currentTicket.AutoDecisionConf = &conf
				currentTicket.AutoDecisionReason = result.Reason
				return tx.Save(&currentTicket).Error
			})

			if err != nil {
				return &AutoDecisionResult{
					Decision:   "blocked",
					Confidence: 0,
					Reason:     fmt.Sprintf("自动判责保存失败: %v", err),
					Rules:      result.Rules,
				}, err
			}

			activity := &models.TicketActivity{
				TicketID:   ticketID,
				Action:     "auto_decision",
				ActionType: "decision",
				Details:    result.Reason,
				CreatedAt:  time.Now(),
			}
			database.DB.Create(activity)
		}
	}

	return result, nil
}

func (s *TicketService) evaluateRule(rule *models.Rule, ticket *models.Ticket, evidences []models.TicketEvidence) (bool, error) {
	var conditions map[string]interface{}
	if err := json.Unmarshal([]byte(rule.Conditions), &conditions); err != nil {
		return false, err
	}

	for key, value := range conditions {
		switch key {
		case "evidence_count":
			if cond, ok := value.(map[string]interface{}); ok {
				if gte, ok := cond["$gte"].(float64); ok {
					if len(evidences) < int(gte) {
						return false, nil
					}
				}
			}
		case "category":
			if ticket.Category != value {
				return false, nil
			}
		case "type":
			if ticket.Type != value {
				return false, nil
			}
		}
	}

	return true, nil
}

func (s *TicketService) Arbitrate(ticketID uint, decision string, amount float64, reason string, arbitratorID uint) error {
	return database.DB.Transaction(func(tx *gorm.DB) error {
		var ticket models.Ticket
		if err := tx.First(&ticket, ticketID).Error; err != nil {
			return err
		}

		if !ticket.ArbitrationLocked {
			return errors.New("ticket is not locked for arbitration, please escalate first")
		}

		if ticket.ArbitrationLockBy != nil && *ticket.ArbitrationLockBy != arbitratorID {
			return fmt.Errorf("ticket is locked by another arbitrator: %d", *ticket.ArbitrationLockBy)
		}

		if ticket.FinalDecision != nil {
			return ErrFinalDecisionExists
		}

		ticket.FinalDecision = &decision
		ticket.FinalDecisionAmount = &amount
		ticket.FinalDecisionReason = reason
		ticket.Status = "executing"
		ticket.Stage = "executing"

		ticket.ArbitrationLocked = false
		ticket.ArbitrationLockBy = nil
		ticket.ArbitrationLockAt = nil
		ticket.ArbitrationLockReason = ""
		ticket.AutoDecisionPaused = false

		if err := tx.Save(&ticket).Error; err != nil {
			return err
		}

		if err := s.updateSellerScore(ticket.SellerID, ticket.ID, decision, amount); err != nil {
			fmt.Printf("Warning: failed to update seller score: %v\n", err)
		}

		activity := &models.TicketActivity{
			TicketID:   ticketID,
			UserID:     arbitratorID,
			Action:     "arbitrate_and_unlock",
			ActionType: "decision",
			Details:    fmt.Sprintf("仲裁完成，仲裁锁已释放。决定: %s, 金额: %.2f, 原因: %s", decision, amount, reason),
			CreatedAt:  time.Now(),
		}
		if err := tx.Create(activity).Error; err != nil {
			return err
		}

		return nil
	})
}

func (s *TicketService) updateSellerScore(sellerID uint, ticketID uint, decision string, amount float64) error {
	var seller models.Seller
	if err := database.DB.First(&seller, sellerID).Error; err != nil {
		return err
	}

	beforeScore := seller.ServiceScore
	scoreChange := 0.0
	reasonType := ""

	switch decision {
	case "refund", "return", "seller_responsible":
		scoreChange = -2.5
		reasonType = "仲裁败诉"
		seller.DisputeLosses++
	case "reject", "buyer_responsible":
		scoreChange = 0
		reasonType = "仲裁胜诉"
		seller.DisputeWins++
	case "partial_refund":
		scoreChange = -1.0
		reasonType = "部分支持"
	}

	seller.ServiceScore += scoreChange
	if seller.ServiceScore < 0 {
		seller.ServiceScore = 0
	} else if seller.ServiceScore > 100 {
		seller.ServiceScore = 100
	}

	seller.DisputeCount++

	if err := database.DB.Save(&seller).Error; err != nil {
		return err
	}

	history := &models.SellerScoreHistory{
		SellerID:    sellerID,
		TicketID:    ticketID,
		BeforeScore: beforeScore,
		AfterScore:  seller.ServiceScore,
		Change:      scoreChange,
		Reason:      fmt.Sprintf("仲裁决定: %s", decision),
		ReasonType:  reasonType,
		CreatedAt:   time.Now(),
	}

	return database.DB.Create(history).Error
}

func (s *TicketService) GetStatistics(filters map[string]interface{}) (map[string]interface{}, error) {
	var total int64
	var pendingCount int64
	var processingCount int64
	var arbitrationCount int64
	var closedCount int64
	var slaWarningCount int64

	database.DB.Model(&models.Ticket{}).Count(&total)
	database.DB.Model(&models.Ticket{}).Where("status IN ?", []string{"pending", "evidence"}).Count(&pendingCount)
	database.DB.Model(&models.Ticket{}).Where("status = ?", "negotiation").Count(&processingCount)
	database.DB.Model(&models.Ticket{}).Where("status IN ?", []string{"platform", "arbitration"}).Count(&arbitrationCount)
	database.DB.Model(&models.Ticket{}).Where("status = ?", "closed").Count(&closedCount)
	database.DB.Model(&models.Ticket{}).Where("sla_percentage >= ?", 80).Count(&slaWarningCount)

	return map[string]interface{}{
		"total":            total,
		"pending":          pendingCount,
		"processing":       processingCount,
		"arbitration":      arbitrationCount,
		"closed":           closedCount,
		"sla_warning":      slaWarningCount,
		"resolution_rate":  float64(closedCount) / float64(total) * 100,
	}, nil
}

func generateTicketNo() string {
	now := time.Now()
	uuidPart := uuid.New().String()[:6]
	return fmt.Sprintf("WT%s%s", now.Format("20060102"), uuidPart)
}
