package models

import (
	"time"

	"gorm.io/gorm"
)

type User struct {
	ID           uint           `gorm:"primaryKey" json:"id"`
	Username     string         `gorm:"uniqueIndex;size:50;not null" json:"username"`
	Password     string         `gorm:"size:255;not null" json:"-"`
	Name         string         `gorm:"size:50" json:"name"`
	Email        string         `gorm:"size:100" json:"email"`
	Phone        string         `gorm:"size:20" json:"phone"`
	Role         string         `gorm:"size:20;not null" json:"role"`
	Avatar       string         `gorm:"size:255" json:"avatar"`
	IsActive     bool           `gorm:"default:true" json:"is_active"`
	CreatedAt    time.Time      `json:"created_at"`
	UpdatedAt    time.Time      `json:"updated_at"`
	DeletedAt    gorm.DeletedAt `gorm:"index" json:"-"`
}

type UserProfile struct {
	ID            uint      `gorm:"primaryKey" json:"id"`
	UserID        uint      `gorm:"uniqueIndex;not null" json:"user_id"`
	User          User      `gorm:"foreignKey:UserID" json:"user,omitempty"`
	CreditScore   int       `gorm:"default:100" json:"credit_score"`
	DisputeCount  int       `gorm:"default:0" json:"dispute_count"`
	WinCount      int       `gorm:"default:0" json:"win_count"`
	LoseCount     int       `gorm:"default:0" json:"lose_count"`
	TotalSpent    float64   `gorm:"default:0" json:"total_spent"`
	LastActiveAt  time.Time `json:"last_active_at"`
	CreatedAt     time.Time `json:"created_at"`
	UpdatedAt     time.Time `json:"updated_at"`
}

type Seller struct {
	ID              uint      `gorm:"primaryKey" json:"id"`
	UserID          uint      `gorm:"uniqueIndex;not null" json:"user_id"`
	User            User      `gorm:"foreignKey:UserID" json:"user,omitempty"`
	ShopName        string    `gorm:"size:100;not null" json:"shop_name"`
	ShopLogo        string    `gorm:"size:255" json:"shop_logo"`
	ServiceScore    float64   `gorm:"default:100" json:"service_score"`
	DisputeCount    int       `gorm:"default:0" json:"dispute_count"`
	DisputeWins     int       `gorm:"default:0" json:"dispute_wins"`
	DisputeLosses   int       `gorm:"default:0" json:"dispute_losses"`
	AvgResolveHours float64   `gorm:"default:24" json:"avg_resolve_hours"`
	IsVerified      bool      `gorm:"default:false" json:"is_verified"`
	IsPremium       bool      `gorm:"default:false" json:"is_premium"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}

type Order struct {
	ID           uint      `gorm:"primaryKey" json:"id"`
	OrderNo      string    `gorm:"uniqueIndex;size:32;not null" json:"order_no"`
	BuyerID      uint      `gorm:"not null" json:"buyer_id"`
	Buyer        User      `gorm:"foreignKey:BuyerID" json:"buyer,omitempty"`
	SellerID     uint      `gorm:"not null" json:"seller_id"`
	Seller       Seller    `gorm:"foreignKey:SellerID" json:"seller,omitempty"`
	ProductName  string    `gorm:"size:255;not null" json:"product_name"`
	ProductID    uint      `gorm:"not null" json:"product_id"`
	ProductImage string    `gorm:"size:255" json:"product_image"`
	Quantity     int       `gorm:"default:1;not null" json:"quantity"`
	UnitPrice    float64   `gorm:"not null" json:"unit_price"`
	TotalAmount  float64   `gorm:"not null" json:"total_amount"`
	Status       string    `gorm:"size:20;default:'pending'" json:"status"`
	PayTime      time.Time `json:"pay_time"`
	ShipTime     time.Time `json:"ship_time"`
	ReceiveTime  time.Time `json:"receive_time"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
}

type Ticket struct {
	ID                  uint       `gorm:"primaryKey" json:"id"`
	TicketNo            string     `gorm:"uniqueIndex;size:20;not null" json:"ticket_no"`
	OrderID             uint       `gorm:"not null" json:"order_id"`
	Order               Order      `gorm:"foreignKey:OrderID" json:"order,omitempty"`
	BuyerID             uint       `gorm:"not null" json:"buyer_id"`
	Buyer               User       `gorm:"foreignKey:BuyerID" json:"buyer,omitempty"`
	SellerID            uint       `gorm:"not null" json:"seller_id"`
	Seller              Seller     `gorm:"foreignKey:SellerID" json:"seller,omitempty"`
	Type                string     `gorm:"size:20;not null" json:"type"`
	Category            string     `gorm:"size:50" json:"category"`
	SubCategory         string     `gorm:"size:50" json:"sub_category"`
	Title               string     `gorm:"size:255;not null" json:"title"`
	Description         string     `gorm:"type:text" json:"description"`
	RequestAmount       float64    `gorm:"not null" json:"request_amount"`
	Status              string     `gorm:"size:20;default:'pending'" json:"status"`
	Stage               string     `gorm:"size:20;default:'evidence'" json:"stage"`
	ArbitratorID        *uint      `json:"arbitrator_id"`
	Arbitrator          *User      `gorm:"foreignKey:ArbitratorID" json:"arbitrator,omitempty"`
	AutoDecision        *string    `gorm:"size:50" json:"auto_decision"`
	AutoDecisionConf    *int       `json:"auto_decision_conf"`
	AutoDecisionReason  string     `gorm:"type:text" json:"auto_decision_reason"`
	FinalDecision       *string    `gorm:"size:50" json:"final_decision"`
	FinalDecisionAmount *float64   `json:"final_decision_amount"`
	FinalDecisionReason string     `gorm:"type:text" json:"final_decision_reason"`
	SLAStartTime        time.Time  `json:"sla_start_time"`
	SLAEndTime          time.Time  `json:"sla_end_time"`
	SLARemainingHours   float64    `json:"sla_remaining_hours"`
	SLAPercentage       float64    `json:"sla_percentage"`
	SLAWarningSent      bool       `gorm:"default:false" json:"sla_warning_sent"`
	SLACriticalSent     bool       `gorm:"default:false" json:"sla_critical_sent"`
	IsEscalated         bool       `gorm:"default:false" json:"is_escalated"`
	EscalatedReason     string     `gorm:"type:text" json:"escalated_reason"`
	EscalatedAt         *time.Time `json:"escalated_at"`
	EvidenceSubmittedAt *time.Time `json:"evidence_submitted_at"`
	NegotiationStartAt  *time.Time `json:"negotiation_start_at"`
	ArbitrationStartAt  *time.Time `json:"arbitration_start_at"`
	ClosedAt            *time.Time `json:"closed_at"`

	ArbitrationLocked     bool       `gorm:"default:false" json:"arbitration_locked"`
	ArbitrationLockBy     *uint      `json:"arbitration_lock_by"`
	ArbitrationLockAt     *time.Time `json:"arbitration_lock_at"`
	ArbitrationLockReason string     `gorm:"type:text" json:"arbitration_lock_reason"`
	AutoDecisionPaused    bool       `gorm:"default:false" json:"auto_decision_paused"`

	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type AnalysisRequest struct {
	ID              uint       `gorm:"primaryKey" json:"id"`
	RequestID       string     `gorm:"uniqueIndex;size:36;not null" json:"request_id"`
	TicketID        uint       `gorm:"not null;index" json:"ticket_id"`
	Ticket          Ticket     `gorm:"foreignKey:TicketID" json:"ticket,omitempty"`
	EvidenceID      uint       `gorm:"not null;uniqueIndex" json:"evidence_id"`
	Evidence        TicketEvidence `gorm:"foreignKey:EvidenceID" json:"evidence,omitempty"`
	Status          string     `gorm:"size:20;default:'pending'" json:"status"`
	AnalysisType    string     `gorm:"size:50" json:"analysis_type"`
	ErrorCode       string     `gorm:"size:100" json:"error_code"`
	ErrorMessage    string     `gorm:"type:text" json:"error_message"`
	RetryCount      int        `gorm:"default:0" json:"retry_count"`
	RequestedAt     time.Time  `json:"requested_at"`
	CompletedAt     *time.Time `json:"completed_at"`
	CallbackURL     string     `gorm:"size:500" json:"callback_url"`
	CreatedAt       time.Time  `json:"created_at"`
	UpdatedAt       time.Time  `json:"updated_at"`
}

type TicketEvidence struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	TicketID    uint      `gorm:"not null;index" json:"ticket_id"`
	Ticket      Ticket    `gorm:"foreignKey:TicketID" json:"ticket,omitempty"`
	UserID      uint      `gorm:"not null" json:"user_id"`
	User        User      `gorm:"foreignKey:UserID" json:"user,omitempty"`
	Type        string    `gorm:"size:20;not null" json:"type"`
	FileName    string    `gorm:"size:255;not null" json:"file_name"`
	FileSize    int64     `json:"file_size"`
	FileURL     string    `gorm:"size:500;not null" json:"file_url"`
	Thumbnail   string    `gorm:"size:500" json:"thumbnail"`
	MimeType    string    `gorm:"size:100" json:"mime_type"`
	Description string    `gorm:"type:text" json:"description"`
	IsAnalyzed  bool      `gorm:"default:false" json:"is_analyzed"`
	Analysis    string    `gorm:"type:text" json:"analysis"`
	AnalysisScore float64  `json:"analysis_score"`
	AnalysisRequestID string `gorm:"size:36;index" json:"analysis_request_id"`
	AnalysisStatus    string `gorm:"size:20;default:'pending'" json:"analysis_status"`
	CreatedAt   time.Time `json:"created_at"`
}

type TicketMessage struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	TicketID    uint      `gorm:"not null;index" json:"ticket_id"`
	Ticket      Ticket    `gorm:"foreignKey:TicketID" json:"ticket,omitempty"`
	UserID      uint      `gorm:"not null" json:"user_id"`
	User        User      `gorm:"foreignKey:UserID" json:"user,omitempty"`
	FromType    string    `gorm:"size:20;not null" json:"from_type"`
	Content     string    `gorm:"type:text;not null" json:"content"`
	MessageType string    `gorm:"size:20;default:'text'" json:"message_type"`
	IsSystem    bool      `gorm:"default:false" json:"is_system"`
	CreatedAt   time.Time `json:"created_at"`
}

type TicketActivity struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	TicketID    uint      `gorm:"not null;index" json:"ticket_id"`
	Ticket      Ticket    `gorm:"foreignKey:TicketID" json:"ticket,omitempty"`
	UserID      uint      `json:"user_id"`
	Action      string    `gorm:"size:50;not null" json:"action"`
	ActionType  string    `gorm:"size:20;not null" json:"action_type"`
	Details     string    `gorm:"type:text" json:"details"`
	FromStatus  string    `gorm:"size:20" json:"from_status"`
	ToStatus    string    `gorm:"size:20" json:"to_status"`
	CreatedAt   time.Time `json:"created_at"`
}

type Rule struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	Name        string    `gorm:"size:100;not null" json:"name"`
	Code        string    `gorm:"uniqueIndex;size:50;not null" json:"code"`
	Category    string    `gorm:"size:50;not null" json:"category"`
	Description string    `gorm:"type:text" json:"description"`
	Conditions  string    `gorm:"type:text;not null" json:"conditions"`
	Actions     string    `gorm:"type:text;not null" json:"actions"`
	Priority    int       `gorm:"default:0" json:"priority"`
	Weight      int       `gorm:"default:100" json:"weight"`
	IsActive    bool      `gorm:"default:true" json:"is_active"`
	Version     int       `gorm:"default:1" json:"version"`
	CreatedBy   uint      `json:"created_by"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

type Case struct {
	ID             uint      `gorm:"primaryKey" json:"id"`
	CaseNo         string    `gorm:"uniqueIndex;size:20;not null" json:"case_no"`
	Title          string    `gorm:"size:255;not null" json:"title"`
	Category       string    `gorm:"size:50" json:"category"`
	SubCategory    string    `gorm:"size:50" json:"sub_category"`
	Description    string    `gorm:"type:text" json:"description"`
	Facts          string    `gorm:"type:text" json:"facts"`
	Evidence       string    `gorm:"type:text" json:"evidence"`
	Decision       string    `gorm:"size:50;not null" json:"decision"`
	DecisionReason string    `gorm:"type:text" json:"decision_reason"`
	RulesApplied   string    `gorm:"type:text" json:"rules_applied"`
	IsPublic       bool      `gorm:"default:true" json:"is_public"`
	ViewCount      int       `gorm:"default:0" json:"view_count"`
	ReferenceCount int       `gorm:"default:0" json:"reference_count"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

type CaseTag struct {
	ID      uint   `gorm:"primaryKey" json:"id"`
	CaseID  uint   `gorm:"not null;index" json:"case_id"`
	Tag     string `gorm:"size:50;not null" json:"tag"`
	Weight  int    `gorm:"default:1" json:"weight"`
}

type SellerScoreHistory struct {
	ID            uint      `gorm:"primaryKey" json:"id"`
	SellerID      uint      `gorm:"not null;index" json:"seller_id"`
	Seller        Seller    `gorm:"foreignKey:SellerID" json:"seller,omitempty"`
	TicketID      uint      `gorm:"index" json:"ticket_id"`
	BeforeScore   float64   `json:"before_score"`
	AfterScore    float64   `json:"after_score"`
	Change        float64   `json:"change"`
	Reason        string    `gorm:"type:text" json:"reason"`
	ReasonType    string    `gorm:"size:50" json:"reason_type"`
	CreatedAt     time.Time `json:"created_at"`
}

type SLAAlert struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	TicketID    uint      `gorm:"not null;index" json:"ticket_id"`
	Ticket      Ticket    `gorm:"foreignKey:TicketID" json:"ticket,omitempty"`
	AlertType   string    `gorm:"size:20;not null" json:"alert_type"`
	Level       string    `gorm:"size:20;not null" json:"level"`
	Message     string    `gorm:"type:text" json:"message"`
	Stage       string    `gorm:"size:20" json:"stage"`
	Remaining   float64   `json:"remaining_hours"`
	IsResolved  bool      `gorm:"default:false" json:"is_resolved"`
	ResolvedAt  *time.Time `json:"resolved_at"`
	CreatedAt   time.Time  `json:"created_at"`
}

type ImageAnalysis struct {
	ID              uint      `gorm:"primaryKey" json:"id"`
	EvidenceID      uint      `gorm:"uniqueIndex;not null" json:"evidence_id"`
	Evidence        TicketEvidence `gorm:"foreignKey:EvidenceID" json:"evidence,omitempty"`
	AnalysisType    string    `gorm:"size:50;not null" json:"analysis_type"`
	HasIssue        bool      `gorm:"default:false" json:"has_issue"`
	IssueType       string    `gorm:"size:50" json:"issue_type"`
	Confidence      float64   `json:"confidence"`
	Description     string    `gorm:"type:text" json:"description"`
	Details         string    `gorm:"type:text" json:"details"`
	TextExtracted   string    `gorm:"type:text" json:"text_extracted"`
	HasFalseClaim   bool      `gorm:"default:false" json:"has_false_claim"`
	FalseClaimType  string    `gorm:"size:50" json:"false_claim_type"`
	CreatedAt       time.Time `json:"created_at"`
}

func (User) TableName() string          { return "users" }
func (UserProfile) TableName() string   { return "user_profiles" }
func (Seller) TableName() string        { return "sellers" }
func (Order) TableName() string         { return "orders" }
func (Ticket) TableName() string        { return "tickets" }
func (AnalysisRequest) TableName() string { return "analysis_requests" }
func (TicketEvidence) TableName() string { return "ticket_evidences" }
func (TicketMessage) TableName() string  { return "ticket_messages" }
func (TicketActivity) TableName() string { return "ticket_activities" }
func (Rule) TableName() string          { return "rules" }
func (Case) TableName() string          { return "cases" }
func (CaseTag) TableName() string       { return "case_tags" }
func (SellerScoreHistory) TableName() string { return "seller_score_histories" }
func (SLAAlert) TableName() string      { return "sla_alerts" }
func (ImageAnalysis) TableName() string { return "image_analyses" }
