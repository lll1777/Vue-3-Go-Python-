package main

import (
	"ecommerce-dispute-platform/config"
	"ecommerce-dispute-platform/database"
	"ecommerce-dispute-platform/router"
	"ecommerce-dispute-platform/services"
	"fmt"
	"log"
	"os"

	"github.com/gin-gonic/gin"
	"gopkg.in/natefinch/lumberjack.v2"
)

func main() {
	fmt.Println("=== 智能电商维权与退换货工单仲裁平台 ===")
	fmt.Println("正在启动服务...")

	if err := config.Init(); err != nil {
		log.Fatalf("配置初始化失败: %v", err)
	}

	setupLogging()

	if err := database.Init(); err != nil {
		log.Fatalf("数据库初始化失败: %v", err)
	}

	slaService := services.NewSLAService()
	slaService.Start()
	defer slaService.Stop()

	gin.SetMode(config.AppConfig.Server.Mode)
	r := router.SetupRouter()

	port := config.AppConfig.Server.Port
	fmt.Printf("服务启动成功，监听端口: %d\n", port)
	fmt.Printf("模式: %s\n", config.AppConfig.Server.Mode)
	fmt.Println("===========================================")

	if err := r.Run(fmt.Sprintf(":%d", port)); err != nil {
		log.Fatalf("服务启动失败: %v", err)
	}
}

func setupLogging() {
	logConfig := config.AppConfig.Log

	log.SetOutput(&lumberjack.Logger{
		Filename:   logConfig.Filename,
		MaxSize:    logConfig.MaxSize,
		MaxBackups: logConfig.MaxBackups,
		MaxAge:     logConfig.MaxAge,
		Compress:   true,
		LocalTime:  true,
	})

	log.SetFlags(log.LstdFlags | log.Lshortfile)

	fmt.Println("日志系统已初始化")
}

func init() {
	if err := os.MkdirAll("./data", 0755); err != nil {
		log.Printf("创建数据目录失败: %v", err)
	}
	if err := os.MkdirAll("./logs", 0755); err != nil {
		log.Printf("创建日志目录失败: %v", err)
	}
	if err := os.MkdirAll("./uploads/evidence", 0755); err != nil {
		log.Printf("创建上传目录失败: %v", err)
	}
}
