package handlers

import (
	"ecommerce-dispute-platform/database"
	"ecommerce-dispute-platform/middleware"
	"ecommerce-dispute-platform/models"
	"ecommerce-dispute-platform/services"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

type CreateTicketRequest struct {
	OrderID       uint    `json:"order_id" binding:"required"`
	Type          string  `json:"type" binding:"required"`
	Category      string  `json:"category"`
	Title         string  `json:"title" binding:"required"`
	Description   string  `json:"description" binding:"required"`
	RequestAmount float64 `json:"request_amount" binding:"required"`
}

type UpdateStatusRequest struct {
	Status string `json:"status" binding:"required"`
	Stage  string `json:"stage"`
	Reason string `json:"reason"`
}

type SendMessageRequest struct {
	Content     string `json:"content" binding:"required"`
	MessageType string `json:"message_type"`
}

type ArbitrateRequest struct {
	Decision string  `json:"decision" binding:"required"`
	Amount   float64 `json:"amount"`
	Reason   string  `json:"reason"`
}

type EscalateRequest struct {
	Reason string `json:"reason"`
}

var ticketService = services.NewTicketService()
var slaService = services.NewSLAService()
var analysisService = services.NewAnalysisService()

func GetTickets(c *gin.Context) {
	userID := middleware.GetCurrentUserID(c)
	userRole := c.GetString("user_role")

	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "10"))

	filters := make(map[string]interface{})
	if ticketNo := c.Query("ticket_no"); ticketNo != "" {
		filters["ticket_no"] = ticketNo
	}
	if orderNo := c.Query("order_no"); orderNo != "" {
		filters["order_no"] = orderNo
	}
	if ticketType := c.Query("type"); ticketType != "" {
		filters["type"] = ticketType
	}
	if status := c.Query("status"); status != "" {
		filters["status"] = status
	}

	tickets, total, err := ticketService.GetTickets(userID, userRole, page, pageSize, filters)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "获取工单列表失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": map[string]interface{}{
			"list":      tickets,
			"total":     total,
			"page":      page,
			"page_size": pageSize,
		},
	})
}

func GetTicket(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的工单ID",
		})
		return
	}

	ticket, err := ticketService.GetTicketByID(uint(id))
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"code":    404,
			"message": "工单不存在",
		})
		return
	}

	userID := middleware.GetCurrentUserID(c)
	userRole := c.GetString("user_role")

	if userRole == "buyer" && ticket.BuyerID != userID {
		c.JSON(http.StatusForbidden, gin.H{
			"code":    403,
			"message": "没有权限查看此工单",
		})
		return
	}
	if userRole == "seller" && ticket.SellerID != userID {
		c.JSON(http.StatusForbidden, gin.H{
			"code":    403,
			"message": "没有权限查看此工单",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": ticket,
	})
}

func CreateTicket(c *gin.Context) {
	var req CreateTicketRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "参数错误",
			"error":   err.Error(),
		})
		return
	}

	userID := middleware.GetCurrentUserID(c)

	var order models.Order
	if err := database.DB.First(&order, req.OrderID).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"code":    404,
			"message": "订单不存在",
		})
		return
	}

	ticket := &models.Ticket{
		OrderID:       req.OrderID,
		BuyerID:       userID,
		SellerID:      order.SellerID,
		Type:          req.Type,
		Category:      req.Category,
		Title:         req.Title,
		Description:   req.Description,
		RequestAmount: req.RequestAmount,
	}

	if err := ticketService.CreateTicket(ticket); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "创建工单失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code":    200,
		"message": "工单创建成功",
		"data":    ticket,
	})
}

func UpdateTicketStatus(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的工单ID",
		})
		return
	}

	var req UpdateStatusRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "参数错误",
		})
		return
	}

	userID := middleware.GetCurrentUserID(c)

	if err := ticketService.UpdateTicketStatus(uint(id), req.Status, req.Stage, userID, req.Reason); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "更新工单状态失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code":    200,
		"message": "状态更新成功",
	})
}

func UploadEvidence(c *gin.Context) {
	userID := middleware.GetCurrentUserID(c)
	ticketIDStr := c.PostForm("ticket_id")
	ticketID, err := strconv.ParseUint(ticketIDStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的工单ID",
		})
		return
	}

	file, header, err := c.Request.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "请选择文件",
		})
		return
	}
	defer file.Close()

	ext := filepath.Ext(header.Filename)
	fileName := fmt.Sprintf("%d_%d%s", time.Now().Unix(), userID, ext)
	filePath := "./uploads/evidence/" + fileName

	out, err := os.Create(filePath)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "保存文件失败",
		})
		return
	}
	defer out.Close()

	_, err = io.Copy(out, file)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "保存文件失败",
		})
		return
	}

	evidence := &models.TicketEvidence{
		TicketID:  uint(ticketID),
		UserID:    userID,
		Type:      "image",
		FileName:  header.Filename,
		FileSize:  header.Size,
		FileURL:   "/uploads/evidence/" + fileName,
		MimeType:  header.Header.Get("Content-Type"),
		CreatedAt: time.Now(),
	}

	if err := ticketService.SubmitEvidence(uint(ticketID), evidence); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "提交证据失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code":    200,
		"message": "证据上传成功",
		"data":    evidence,
	})
}

func GetMessages(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的工单ID",
		})
		return
	}

	page, _ := strconv.Atoi(c.DefaultQuery("page", "1"))
	pageSize, _ := strconv.Atoi(c.DefaultQuery("page_size", "50"))

	messages, total, err := ticketService.GetMessages(uint(id), page, pageSize)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "获取消息失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": map[string]interface{}{
			"list":      messages,
			"total":     total,
			"page":      page,
			"page_size": pageSize,
		},
	})
}

func SendMessage(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的工单ID",
		})
		return
	}

	var req SendMessageRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "参数错误",
		})
		return
	}

	userID := middleware.GetCurrentUserID(c)
	userRole := c.GetString("user_role")

	message := &models.TicketMessage{
		UserID:      userID,
		FromType:    userRole,
		Content:     req.Content,
		MessageType: req.MessageType,
		IsSystem:    false,
		CreatedAt:   time.Now(),
	}

	if err := ticketService.AddMessage(uint(id), message); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "发送消息失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code":    200,
		"message": "消息发送成功",
		"data":    message,
	})
}

func EscalateTicket(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的工单ID",
		})
		return
	}

	var req EscalateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "参数错误",
		})
		return
	}

	arbitratorID := uint(6)

	if err := ticketService.Escalate(uint(id), arbitratorID, req.Reason); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "升级工单失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code":    200,
		"message": "工单已升级到平台仲裁",
	})
}

func AutoDecide(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的工单ID",
		})
		return
	}

	result, err := ticketService.AutoDecide(uint(id))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "自动判定失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": result,
	})
}

func Arbitrate(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的工单ID",
		})
		return
	}

	var req ArbitrateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "参数错误",
		})
		return
	}

	userID := middleware.GetCurrentUserID(c)

	if err := ticketService.Arbitrate(uint(id), req.Decision, req.Amount, req.Reason, userID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "仲裁失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code":    200,
		"message": "仲裁完成",
	})
}

func GetSLAMonitor(c *gin.Context) {
	filters := make(map[string]interface{})
	if stage := c.Query("stage"); stage != "" {
		filters["stage"] = stage
	}
	if slaStatus := c.Query("sla_status"); slaStatus != "" {
		filters["sla_status"] = slaStatus
	}

	data, err := slaService.GetSLAMonitoring(filters)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "获取SLA监控失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": data,
	})
}

func GetStatistics(c *gin.Context) {
	filters := make(map[string]interface{})
	if startDate := c.Query("start_date"); startDate != "" {
		filters["start_date"] = startDate
	}
	if endDate := c.Query("end_date"); endDate != "" {
		filters["end_date"] = endDate
	}

	data, err := ticketService.GetStatistics(filters)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "获取统计数据失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": data,
	})
}

func GetSimilarCases(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的工单ID",
		})
		return
	}

	var ticket models.Ticket
	if err := database.DB.First(&ticket, uint(id)).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"code":    404,
			"message": "工单不存在",
		})
		return
	}

	var similarCases []models.Case
	database.DB.Where("category = ? AND is_public = ?", ticket.Category, true).
		Order("reference_count DESC, view_count DESC").
		Limit(5).
		Find(&similarCases)

	result := make([]map[string]interface{}, 0)
	for _, cs := range similarCases {
		result = append(result, map[string]interface{}{
			"id":             cs.ID,
			"case_no":        cs.CaseNo,
			"title":          cs.Title,
			"category":       cs.Category,
			"decision":       cs.Decision,
			"decision_reason": cs.DecisionReason,
			"view_count":     cs.ViewCount,
			"reference_count": cs.ReferenceCount,
			"similarity":     85,
		})
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": result,
	})
}

type AnalysisCallbackRequest struct {
	RequestID   string      `json:"request_id" binding:"required"`
	TicketID    uint        `json:"ticket_id" binding:"required"`
	EvidenceID  uint        `json:"evidence_id" binding:"required"`
	Status      string      `json:"status" binding:"required"`
	Result      interface{} `json:"result"`
	Error       string      `json:"error"`
	CompletedAt string      `json:"completed_at"`
}

func AnalysisCallback(c *gin.Context) {
	var req AnalysisCallbackRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "参数错误",
			"error":   err.Error(),
		})
		return
	}

	callbackData := &services.AnalysisCallbackData{
		RequestID:   req.RequestID,
		TicketID:    req.TicketID,
		EvidenceID:  req.EvidenceID,
		Status:      req.Status,
		Result:      req.Result,
		Error:       req.Error,
		CompletedAt: req.CompletedAt,
	}

	if err := analysisService.ProcessCallback(callbackData); err != nil {
		if err == services.ErrAnalysisRequestNotFound {
			c.JSON(http.StatusNotFound, gin.H{
				"code":    404,
				"message": "分析请求不存在",
			})
			return
		}
		if err == services.ErrRequestIDMismatch {
			c.JSON(http.StatusBadRequest, gin.H{
				"code":    400,
				"message": "请求ID不匹配",
			})
			return
		}
		if err == services.ErrTicketIDMismatch {
			c.JSON(http.StatusBadRequest, gin.H{
				"code":    400,
				"message": "工单ID不匹配",
			})
			return
		}
		if err == services.ErrAnalysisAlreadyCompleted {
			c.JSON(http.StatusConflict, gin.H{
				"code":    409,
				"message": "分析请求已处理完成",
			})
			return
		}

		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "处理回调失败",
			"error":   err.Error(),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code":    200,
		"message": "回调处理成功",
	})
}

func GetAnalysisStatus(c *gin.Context) {
	requestID := c.Param("request_id")
	if requestID == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "缺少请求ID",
		})
		return
	}

	request, err := analysisService.GetAnalysisStatus(requestID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"code":    404,
			"message": "分析请求不存在",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": request,
	})
}

func GetTicketAnalysisStatus(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的工单ID",
		})
		return
	}

	analyses, err := analysisService.GetTicketAnalyses(uint(id))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "获取分析状态失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": analyses,
	})
}
