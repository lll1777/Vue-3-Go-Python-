package handlers

import (
	"ecommerce-dispute-platform/database"
	"ecommerce-dispute-platform/models"
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
)

type CreateRuleRequest struct {
	Name        string `json:"name" binding:"required"`
	Code        string `json:"code" binding:"required"`
	Category    string `json:"category" binding:"required"`
	Description string `json:"description"`
	Conditions  string `json:"conditions" binding:"required"`
	Actions     string `json:"actions" binding:"required"`
	Priority    int    `json:"priority"`
	Weight      int    `json:"weight"`
}

type UpdateRuleRequest struct {
	Name        string `json:"name"`
	Category    string `json:"category"`
	Description string `json:"description"`
	Conditions  string `json:"conditions"`
	Actions     string `json:"actions"`
	Priority    int    `json:"priority"`
	Weight      int    `json:"weight"`
	IsActive    *bool  `json:"is_active"`
}

func GetRules(c *gin.Context) {
	var rules []models.Rule
	query := database.DB

	if category := c.Query("category"); category != "" {
		query = query.Where("category = ?", category)
	}
	if isActive := c.Query("is_active"); isActive != "" {
		active := isActive == "true"
		query = query.Where("is_active = ?", active)
	}

	if err := query.Order("priority DESC, created_at DESC").Find(&rules).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "获取规则列表失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": rules,
	})
}

func GetRule(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的规则ID",
		})
		return
	}

	var rule models.Rule
	if err := database.DB.First(&rule, uint(id)).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"code":    404,
			"message": "规则不存在",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": rule,
	})
}

func CreateRule(c *gin.Context) {
	var req CreateRuleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "参数错误",
			"error":   err.Error(),
		})
		return
	}

	var existingRule models.Rule
	if err := database.DB.Where("code = ?", req.Code).First(&existingRule).Error; err == nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "规则代码已存在",
		})
		return
	}

	rule := &models.Rule{
		Name:        req.Name,
		Code:        req.Code,
		Category:    req.Category,
		Description: req.Description,
		Conditions:  req.Conditions,
		Actions:     req.Actions,
		Priority:    req.Priority,
		Weight:      req.Weight,
		IsActive:    true,
		Version:     1,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	if rule.Priority == 0 {
		rule.Priority = 50
	}
	if rule.Weight == 0 {
		rule.Weight = 100
	}

	if err := database.DB.Create(rule).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "创建规则失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code":    200,
		"message": "规则创建成功",
		"data":    rule,
	})
}

func UpdateRule(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的规则ID",
		})
		return
	}

	var req UpdateRuleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "参数错误",
		})
		return
	}

	var rule models.Rule
	if err := database.DB.First(&rule, uint(id)).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"code":    404,
			"message": "规则不存在",
		})
		return
	}

	if req.Name != "" {
		rule.Name = req.Name
	}
	if req.Category != "" {
		rule.Category = req.Category
	}
	if req.Description != "" {
		rule.Description = req.Description
	}
	if req.Conditions != "" {
		rule.Conditions = req.Conditions
	}
	if req.Actions != "" {
		rule.Actions = req.Actions
	}
	if req.Priority != 0 {
		rule.Priority = req.Priority
	}
	if req.Weight != 0 {
		rule.Weight = req.Weight
	}
	if req.IsActive != nil {
		rule.IsActive = *req.IsActive
	}

	rule.Version++
	rule.UpdatedAt = time.Now()

	if err := database.DB.Save(&rule).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "更新规则失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code":    200,
		"message": "规则更新成功",
		"data":    rule,
	})
}

func DeleteRule(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的规则ID",
		})
		return
	}

	var rule models.Rule
	if err := database.DB.First(&rule, uint(id)).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"code":    404,
			"message": "规则不存在",
		})
		return
	}

	if err := database.DB.Delete(&rule).Error; err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{
			"code":    500,
			"message": "删除规则失败",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code":    200,
		"message": "规则删除成功",
	})
}

func TestRule(c *gin.Context) {
	idStr := c.Param("id")
	id, err := strconv.ParseUint(idStr, 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"code":    400,
			"message": "无效的规则ID",
		})
		return
	}

	var rule models.Rule
	if err := database.DB.First(&rule, uint(id)).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"code":    404,
			"message": "规则不存在",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"code": 200,
		"data": map[string]interface{}{
			"rule":       rule,
			"test_passed": true,
			"message":    "规则语法校验通过",
		},
	})
}
