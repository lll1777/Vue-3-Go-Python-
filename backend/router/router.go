package router

import (
	"ecommerce-dispute-platform/handlers"
	"ecommerce-dispute-platform/middleware"

	"github.com/gin-gonic/gin"
)

func SetupRouter() *gin.Engine {
	r := gin.Default()

	r.Use(gin.Logger())
	r.Use(gin.Recovery())

	r.Static("/uploads", "./uploads")

	api := r.Group("/api")
	{
		auth := api.Group("/auth")
		{
			auth.POST("/login", handlers.Login)
			auth.POST("/register", handlers.Register)
			auth.POST("/logout", handlers.Logout)
			auth.GET("/me", middleware.JWTAuth(), handlers.GetCurrentUser)
		}

		tickets := api.Group("/tickets")
		tickets.Use(middleware.JWTAuth())
		{
			tickets.GET("", handlers.GetTickets)
			tickets.POST("", handlers.CreateTicket)
			tickets.GET("/:id", handlers.GetTicket)
			tickets.PUT("/:id/status", handlers.UpdateTicketStatus)
			tickets.POST("/:id/evidence", handlers.UploadEvidence)
			tickets.GET("/:id/messages", handlers.GetMessages)
			tickets.POST("/:id/messages", handlers.SendMessage)
			tickets.POST("/:id/escalate", handlers.EscalateTicket)
			tickets.POST("/:id/auto-decide", handlers.AutoDecide)
			tickets.POST("/:id/arbitrate", middleware.RequireRole("arbitrator", "admin"), handlers.Arbitrate)
			tickets.GET("/:id/similar-cases", handlers.GetSimilarCases)
		}

		sla := api.Group("/tickets/sla-monitor")
		sla.Use(middleware.JWTAuth(), middleware.RequireRole("admin", "arbitrator"))
		{
			sla.GET("", handlers.GetSLAMonitor)
		}

		stats := api.Group("/tickets/statistics")
		stats.Use(middleware.JWTAuth(), middleware.RequireRole("admin", "arbitrator"))
		{
			stats.GET("", handlers.GetStatistics)
		}

		rules := api.Group("/rules")
		rules.Use(middleware.JWTAuth(), middleware.RequireRole("admin"))
		{
			rules.GET("", handlers.GetRules)
			rules.POST("", handlers.CreateRule)
			rules.GET("/:id", handlers.GetRule)
			rules.PUT("/:id", handlers.UpdateRule)
			rules.DELETE("/:id", handlers.DeleteRule)
			rules.POST("/:id/test", handlers.TestRule)
		}

		evidence := api.Group("/evidence")
		evidence.Use(middleware.JWTAuth())
		{
			evidence.POST("/upload", handlers.UploadEvidence)
		}
	}

	return r
}
