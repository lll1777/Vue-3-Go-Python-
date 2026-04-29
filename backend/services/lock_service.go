package services

import (
	"ecommerce-dispute-platform/database"
	"ecommerce-dispute-platform/models"
	"errors"
	"fmt"
	"time"

	"gorm.io/gorm"
)

var (
	ErrTicketAlreadyLocked    = errors.New("ticket is already locked by another arbitrator")
	ErrTicketNotLocked        = errors.New("ticket is not locked")
	ErrLockNotOwned           = errors.New("lock not owned by this arbitrator")
	ErrAutoDecisionPaused     = errors.New("auto decision is paused due to arbitration")
	ErrFinalDecisionExists    = errors.New("final decision already exists")
)

type LockService struct{}

type LockAcquireResult struct {
	Success   bool          `json:"success"`
	Message   string        `json:"message"`
	LockedBy  *uint         `json:"locked_by,omitempty"`
	LockedAt  *time.Time    `json:"locked_at,omitempty"`
}

func NewLockService() *LockService {
	return &LockService{}
}

func (s *LockService) AcquireLock(tx *gorm.DB, ticketID uint, arbitratorID uint, reason string) (*LockAcquireResult, error) {
	var ticket models.Ticket
	if err := tx.First(&ticket, ticketID).Error; err != nil {
		return nil, err
	}

	if ticket.ArbitrationLocked {
		if ticket.ArbitrationLockBy != nil && *ticket.ArbitrationLockBy == arbitratorID {
			return &LockAcquireResult{
				Success:  true,
				Message:  "lock already acquired by current arbitrator",
				LockedBy: ticket.ArbitrationLockBy,
				LockedAt: ticket.ArbitrationLockAt,
			}, nil
		}
		return &LockAcquireResult{
			Success:  false,
			Message:  fmt.Sprintf("ticket is locked by arbitrator %d", *ticket.ArbitrationLockBy),
			LockedBy: ticket.ArbitrationLockBy,
			LockedAt: ticket.ArbitrationLockAt,
		}, ErrTicketAlreadyLocked
	}

	now := time.Now()
	ticket.ArbitrationLocked = true
	ticket.ArbitrationLockBy = &arbitratorID
	ticket.ArbitrationLockAt = &now
	ticket.ArbitrationLockReason = reason
	ticket.AutoDecisionPaused = true

	if err := tx.Save(&ticket).Error; err != nil {
		return nil, err
	}

	activity := &models.TicketActivity{
		TicketID:   ticketID,
		UserID:     arbitratorID,
		Action:     "acquire_lock",
		ActionType: "lock",
		Details:    fmt.Sprintf("仲裁锁已获取，原因: %s", reason),
		CreatedAt:  time.Now(),
	}
	if err := tx.Create(activity).Error; err != nil {
		return nil, err
	}

	return &LockAcquireResult{
		Success:  true,
		Message:  "lock acquired successfully",
		LockedBy: &arbitratorID,
		LockedAt: &now,
	}, nil
}

func (s *LockService) ReleaseLock(tx *gorm.DB, ticketID uint, arbitratorID uint) error {
	var ticket models.Ticket
	if err := tx.First(&ticket, ticketID).Error; err != nil {
		return err
	}

	if !ticket.ArbitrationLocked {
		return ErrTicketNotLocked
	}

	if ticket.ArbitrationLockBy != nil && *ticket.ArbitrationLockBy != arbitratorID {
		return ErrLockNotOwned
	}

	ticket.ArbitrationLocked = false
	ticket.ArbitrationLockBy = nil
	ticket.ArbitrationLockAt = nil
	ticket.ArbitrationLockReason = ""
	ticket.AutoDecisionPaused = false

	if err := tx.Save(&ticket).Error; err != nil {
		return err
	}

	activity := &models.TicketActivity{
		TicketID:   ticketID,
		UserID:     arbitratorID,
		Action:     "release_lock",
		ActionType: "unlock",
		Details:    "仲裁锁已释放",
		CreatedAt:  time.Now(),
	}
	if err := tx.Create(activity).Error; err != nil {
		return err
	}

	return nil
}

func (s *LockService) IsLocked(ticketID uint) (bool, error) {
	var ticket models.Ticket
	if err := database.DB.First(&ticket, ticketID).Error; err != nil {
		return false, err
	}
	return ticket.ArbitrationLocked, nil
}

func (s *LockService) GetLockInfo(ticketID uint) (*models.Ticket, error) {
	var ticket models.Ticket
	if err := database.DB.First(&ticket, ticketID).Error; err != nil {
		return nil, err
	}
	return &ticket, nil
}

func (s *LockService) CanAutoDecide(ticketID uint) (bool, string) {
	var ticket models.Ticket
	if err := database.DB.First(&ticket, ticketID).Error; err != nil {
		return false, "ticket not found"
	}

	if ticket.ArbitrationLocked {
		return false, fmt.Sprintf("ticket locked by arbitrator %d", *ticket.ArbitrationLockBy)
	}

	if ticket.AutoDecisionPaused {
		return false, "auto decision is paused"
	}

	if ticket.FinalDecision != nil {
		return false, "final decision already exists"
	}

	return true, ""
}

func (s *LockService) PauseAutoDecision(tx *gorm.DB, ticketID uint, arbitratorID uint, reason string) error {
	var ticket models.Ticket
	if err := tx.First(&ticket, ticketID).Error; err != nil {
		return err
	}

	ticket.AutoDecisionPaused = true

	if err := tx.Save(&ticket).Error; err != nil {
		return err
	}

	activity := &models.TicketActivity{
		TicketID:   ticketID,
		UserID:     arbitratorID,
		Action:     "pause_auto_decision",
		ActionType: "update",
		Details:    fmt.Sprintf("自动判责已暂停，原因: %s", reason),
		CreatedAt:  time.Now(),
	}
	if err := tx.Create(activity).Error; err != nil {
		return err
	}

	return nil
}

func (s *LockService) CheckFinalDecisionExists(ticketID uint) bool {
	var ticket models.Ticket
	if err := database.DB.First(&ticket, ticketID).Error; err != nil {
		return false
	}
	return ticket.FinalDecision != nil
}
