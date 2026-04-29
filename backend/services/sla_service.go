package services

import (
	"ecommerce-dispute-platform/config"
	"ecommerce-dispute-platform/database"
	"ecommerce-dispute-platform/models"
	"fmt"
	"time"

	"github.com/robfig/cron/v3"
)

type SLAService struct {
	cron *cron.Cron
}

func NewSLAService() *SLAService {
	return &SLAService{
		cron: cron.New(),
	}
}

func (s *SLAService) Start() {
	s.cron.AddFunc("@every 1m", s.checkSLA)
	s.cron.Start()
}

func (s *SLAService) Stop() {
	s.cron.Stop()
}

func (s *SLAService) checkSLA() {
	var activeTickets []models.Ticket
	database.DB.Where("status NOT IN ?", []string{"closed", "executing"}).Find(&activeTickets)

	now := time.Now()
	slaConfig := config.AppConfig.SLA

	for i := range activeTickets {
		ticket := &activeTickets[i]

		elapsed := now.Sub(ticket.SLAStartTime).Hours()
		totalHours := ticket.SLAEndTime.Sub(ticket.SLAStartTime).Hours()

		if totalHours <= 0 {
			continue
		}

		ticket.SLARemainingHours = totalHours - elapsed
		ticket.SLAPercentage = (elapsed / totalHours) * 100

		if ticket.SLAPercentage >= slaConfig.WarningThreshold*100 && !ticket.SLAWarningSent {
			s.sendSLAAlert(ticket, "warning")
			ticket.SLAWarningSent = true
		}

		if ticket.SLAPercentage >= slaConfig.CriticalThreshold*100 && !ticket.SLACriticalSent {
			s.sendSLAAlert(ticket, "critical")
			ticket.SLACriticalSent = true
		}

		if ticket.SLAPercentage >= 100 {
			s.handleSLATimeout(ticket)
		}

		database.DB.Save(ticket)
	}
}

func (s *SLAService) sendSLAAlert(ticket *models.Ticket, level string) {
	alert := &models.SLAAlert{
		TicketID:  ticket.ID,
		AlertType: "sla_warning",
		Level:     level,
		Message:   fmt.Sprintf("工单 %s 在 %s 阶段即将超时，剩余时间: %.2f 小时", ticket.TicketNo, ticket.Stage, ticket.SLARemainingHours),
		Stage:     ticket.Stage,
		Remaining: ticket.SLARemainingHours,
		IsResolved: false,
		CreatedAt:  time.Now(),
	}

	database.DB.Create(alert)

	fmt.Printf("[SLA Alert] Ticket %s - Level: %s, Stage: %s, Remaining: %.2f hours\n",
		ticket.TicketNo, level, ticket.Stage, ticket.SLARemainingHours)
}

func (s *SLAService) handleSLATimeout(ticket *models.Ticket) {
	fmt.Printf("[SLA Timeout] Ticket %s - Stage: %s has timed out!\n", ticket.TicketNo, ticket.Stage)

	switch ticket.Stage {
	case "negotiation":
		if ticket.Status == "negotiation" {
			ticketService := NewTicketService()
			result, err := ticketService.AutoDecide(ticket.ID)
			if err == nil && result.Decision != "pending" {
				fmt.Printf("[Auto Decision] Ticket %s - Decision: %s (Confidence: %d%%)\n",
					ticket.TicketNo, result.Decision, result.Confidence)
			} else {
				ticket.IsEscalated = true
				ticket.Status = "platform"
				ticket.Stage = "arbitration"
				ticket.EscalatedReason = "协商超时，自动升级平台仲裁"
				ticket.EscalatedAt = &[]time.Time{time.Now()}[0]
			}
		}
	case "arbitration":
		alert := &models.SLAAlert{
			TicketID:  ticket.ID,
			AlertType: "timeout",
			Level:     "critical",
			Message:   fmt.Sprintf("工单 %s 仲裁阶段已超时，请立即处理", ticket.TicketNo),
			Stage:     ticket.Stage,
			Remaining: ticket.SLARemainingHours,
			IsResolved: false,
			CreatedAt:  time.Now(),
		}
		database.DB.Create(alert)
	}
}

func (s *SLAService) GetSLAStatus(ticketID uint) (map[string]interface{}, error) {
	var ticket models.Ticket
	if err := database.DB.First(&ticket, ticketID).Error; err != nil {
		return nil, err
	}

	now := time.Now()
	elapsed := now.Sub(ticket.SLAStartTime).Hours()
	totalHours := ticket.SLAEndTime.Sub(ticket.SLAStartTime).Hours()

	remainingHours := totalHours - elapsed
	percentage := (elapsed / totalHours) * 100

	slaStatus := "normal"
	if percentage >= config.AppConfig.SLA.WarningThreshold*100 {
		slaStatus = "warning"
	}
	if percentage >= config.AppConfig.SLA.CriticalThreshold*100 {
		slaStatus = "critical"
	}
	if percentage >= 100 {
		slaStatus = "timeout"
	}

	return map[string]interface{}{
		"ticket_id":         ticketID,
		"stage":             ticket.Stage,
		"sla_start_time":    ticket.SLAStartTime,
		"sla_end_time":      ticket.SLAEndTime,
		"elapsed_hours":     elapsed,
		"remaining_hours":   remainingHours,
		"percentage":        percentage,
		"status":            slaStatus,
		"warning_sent":      ticket.SLAWarningSent,
		"critical_sent":     ticket.SLACriticalSent,
	}, nil
}

func (s *SLAService) GetSLAMonitoring(filters map[string]interface{}) ([]map[string]interface{}, error) {
	var tickets []models.Ticket
	query := database.DB.Where("status NOT IN ?", []string{"closed"})

	if stage, ok := filters["stage"].(string); ok && stage != "" {
		query = query.Where("stage = ?", stage)
	}
	if slaStatus, ok := filters["sla_status"].(string); ok && slaStatus != "" {
		switch slaStatus {
		case "warning":
			query = query.Where("sla_percentage >= ?", config.AppConfig.SLA.WarningThreshold*100)
		case "critical":
			query = query.Where("sla_percentage >= ?", config.AppConfig.SLA.CriticalThreshold*100)
		case "timeout":
			query = query.Where("sla_percentage >= 100")
		}
	}

	query.Order("sla_percentage DESC").Find(&tickets)

	var result []map[string]interface{}
	for _, ticket := range tickets {
		now := time.Now()
		elapsed := now.Sub(ticket.SLAStartTime).Hours()
		totalHours := ticket.SLAEndTime.Sub(ticket.SLAStartTime).Hours()
		remainingHours := totalHours - elapsed

		slaStatus := "normal"
		if ticket.SLAPercentage >= config.AppConfig.SLA.WarningThreshold*100 {
			slaStatus = "warning"
		}
		if ticket.SLAPercentage >= config.AppConfig.SLA.CriticalThreshold*100 {
			slaStatus = "critical"
		}
		if ticket.SLAPercentage >= 100 {
			slaStatus = "timeout"
		}

		result = append(result, map[string]interface{}{
			"ticket_id":         ticket.ID,
			"ticket_no":         ticket.TicketNo,
			"title":             ticket.Title,
			"type":              ticket.Type,
			"status":            ticket.Status,
			"stage":             ticket.Stage,
			"remaining_hours":   remainingHours,
			"percentage":        ticket.SLAPercentage,
			"sla_status":        slaStatus,
			"sla_end_time":      ticket.SLAEndTime,
		})
	}

	return result, nil
}
