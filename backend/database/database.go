package database

import (
	"ecommerce-dispute-platform/config"
	"ecommerce-dispute-platform/models"
	"time"

	"golang.org/x/crypto/bcrypt"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var DB *gorm.DB

func Init() error {
	var err error
	cfg := config.AppConfig.Database

	DB, err = gorm.Open(sqlite.Open(cfg.DSN), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})
	if err != nil {
		return err
	}

	if err = migrate(); err != nil {
		return err
	}

	if err = seedData(); err != nil {
		return err
	}

	return nil
}

func migrate() error {
	return DB.AutoMigrate(
		&models.User{},
		&models.UserProfile{},
		&models.Seller{},
		&models.Order{},
		&models.Ticket{},
		&models.TicketEvidence{},
		&models.TicketMessage{},
		&models.TicketActivity{},
		&models.Rule{},
		&models.Case{},
		&models.CaseTag{},
		&models.SellerScoreHistory{},
		&models.SLAAlert{},
		&models.ImageAnalysis{},
	)
}

func seedData() error {
	if err := seedUsers(); err != nil {
		return err
	}
	if err := seedRules(); err != nil {
		return err
	}
	if err := seedCases(); err != nil {
		return err
	}
	return nil
}

func hashPassword(password string) string {
	hashed, _ := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(hashed)
}

func seedUsers() error {
	var count int64
	DB.Model(&models.User{}).Count(&count)
	if count > 0 {
		return nil
	}

	users := []models.User{
		{
			Username: "buyer1",
			Password: hashPassword("123456"),
			Name:     "张三",
			Email:    "buyer1@example.com",
			Phone:    "13800138001",
			Role:     "buyer",
			IsActive: true,
		},
		{
			Username: "buyer2",
			Password: hashPassword("123456"),
			Name:     "李四",
			Email:    "buyer2@example.com",
			Phone:    "13800138002",
			Role:     "buyer",
			IsActive: true,
		},
		{
			Username: "seller1",
			Password: hashPassword("123456"),
			Name:     "某某官方旗舰店",
			Email:    "seller1@example.com",
			Phone:    "13900139001",
			Role:     "seller",
			IsActive: true,
		},
		{
			Username: "seller2",
			Password: hashPassword("123456"),
			Name:     "某某专营店",
			Email:    "seller2@example.com",
			Phone:    "13900139002",
			Role:     "seller",
			IsActive: true,
		},
		{
			Username: "admin1",
			Password: hashPassword("123456"),
			Name:     "平台管理员",
			Email:    "admin1@example.com",
			Phone:    "13700137001",
			Role:     "admin",
			IsActive: true,
		},
		{
			Username: "arbitrator1",
			Password: hashPassword("123456"),
			Name:     "仲裁员王",
			Email:    "arbitrator1@example.com",
			Phone:    "13600136001",
			Role:     "arbitrator",
			IsActive: true,
		},
	}

	for i := range users {
		if err := DB.Create(&users[i]).Error; err != nil {
			return err
		}

		if users[i].Role == "buyer" {
			profile := models.UserProfile{
				UserID:       users[i].ID,
				CreditScore:  100,
				DisputeCount: 0,
				WinCount:     0,
				LoseCount:    0,
				TotalSpent:   50000,
				LastActiveAt: time.Now(),
			}
			DB.Create(&profile)
		} else if users[i].Role == "seller" {
			seller := models.Seller{
				UserID:          users[i].ID,
				ShopName:        users[i].Name,
				ServiceScore:    92.5,
				DisputeCount:    15,
				DisputeWins:     12,
				DisputeLosses:   3,
				AvgResolveHours: 12.5,
				IsVerified:      true,
				IsPremium:       true,
			}
			DB.Create(&seller)
		}
	}

	return nil
}

func seedRules() error {
	var count int64
	DB.Model(&models.Rule{}).Count(&count)
	if count > 0 {
		return nil
	}

	rules := []models.Rule{
		{
			Name:        "7天无理由退货",
			Code:        "RULE_001",
			Category:    "refund",
			Description: "商品在7天退货期限内，支持无理由退货",
			Conditions:  `{"days_since_receive": {"$lte": 7}, "type": "return"}`,
			Actions:     `{"decision": "return", "reason": "7天无理由退货"}`,
			Priority:    100,
			Weight:      100,
			IsActive:    true,
			CreatedBy:   5,
		},
		{
			Name:        "质量问题退款",
			Code:        "RULE_002",
			Category:    "quality",
			Description: "图片证据显示存在明确质量问题，支持退款",
			Conditions:  `{"image_analysis.has_issue": true, "evidence_count": {"$gte": 1}}`,
			Actions:     `{"decision": "refund", "reason": "质量问题证据充分"}`,
			Priority:    90,
			Weight:      95,
			IsActive:    true,
			CreatedBy:   5,
		},
		{
			Name:        "虚假宣传判定",
			Code:        "RULE_003",
			Category:    "advertising",
			Description: "检测到虚假宣传内容，判定商家责任",
			Conditions:  `{"image_analysis.has_false_claim": true, "category": "advertising"}`,
			Actions:     `{"decision": "seller_responsible", "reason": "虚假宣传"}`,
			Priority:    95,
			Weight:      98,
			IsActive:    true,
			CreatedBy:   5,
		},
		{
			Name:        "商家超时响应",
			Code:        "RULE_004",
			Category:    "sla",
			Description: "商家在协商期内未响应，自动支持买家诉求",
			Conditions:  `{"stage": "negotiation", "sla_percentage": {"$gte": 100}, "seller_response_count": 0}`,
			Actions:     `{"decision": "refund", "reason": "商家超时未响应"}`,
			Priority:    80,
			Weight:      90,
			IsActive:    true,
			CreatedBy:   5,
		},
		{
			Name:        "商家服务分低于阈值",
			Code:        "RULE_005",
			Category:    "seller_score",
			Description: "商家服务分低于70分，增加买家胜诉权重",
			Conditions:  `{"seller_service_score": {"$lt": 70}}`,
			Actions:     `{"weight_adjust": 20, "reason": "商家服务分过低"}`,
			Priority:    70,
			Weight:      75,
			IsActive:    true,
			CreatedBy:   5,
		},
		{
			Name:        "买家信誉良好",
			Code:        "RULE_006",
			Category:    "buyer_credit",
			Description: "买家信誉分高于90分，增加胜诉权重",
			Conditions:  `{"buyer_credit_score": {"$gte": 90}}`,
			Actions:     `{"weight_adjust": 10, "reason": "买家信誉良好"}`,
			Priority:    60,
			Weight:      70,
			IsActive:    true,
			CreatedBy:   5,
		},
	}

	for i := range rules {
		rules[i].Version = 1
		if err := DB.Create(&rules[i]).Error; err != nil {
			return err
		}
	}

	return nil
}

func seedCases() error {
	var count int64
	DB.Model(&models.Case{}).Count(&count)
	if count > 0 {
		return nil
	}

	cases := []models.Case{
		{
			CaseNo:         "CASE2026001",
			Title:          "手机屏幕划痕退款案例",
			Category:       "quality",
			SubCategory:    "defect",
			Description:    "买家收到手机后发现屏幕有明显划痕，申请退款",
			Facts:          "买家提供了3张清晰的照片证据，显示屏幕存在深度划痕",
			Evidence:       "照片证据、快递签收记录",
			Decision:       "refund",
			DecisionReason: "证据充分，支持退款申请",
			RulesApplied:   "RULE_002",
			IsPublic:       true,
			ViewCount:      156,
			ReferenceCount: 23,
		},
		{
			CaseNo:         "CASE2026002",
			Title:          "虚假宣传案例-续航能力",
			Category:       "advertising",
			SubCategory:    "false",
			Description:    "商品宣传续航48小时，但实际仅12小时",
			Facts:          "买家提供了商品宣传页截图和实际测试数据",
			Evidence:       "宣传截图、测试视频、聊天记录",
			Decision:       "seller_responsible",
			DecisionReason: "检测到虚假宣传，判定商家承担全部责任",
			RulesApplied:   "RULE_003",
			IsPublic:       true,
			ViewCount:      289,
			ReferenceCount: 45,
		},
		{
			CaseNo:         "CASE2026003",
			Title:          "电子产品退货案例",
			Category:       "refund",
			SubCategory:    "return",
			Description:    "买家在7天内申请无理由退货",
			Facts:          "商品在签收后第5天申请退货，商品完好",
			Evidence:       "快递签收记录、商品照片",
			Decision:       "return",
			DecisionReason: "符合7天无理由退货条件",
			RulesApplied:   "RULE_001",
			IsPublic:       true,
			ViewCount:      98,
			ReferenceCount: 12,
		},
	}

	for i := range cases {
		if err := DB.Create(&cases[i]).Error; err != nil {
			return err
		}
	}

	return nil
}
