package config

import (
	"fmt"
	"os"

	"github.com/spf13/viper"
)

type Config struct {
	Server        ServerConfig        `mapstructure:"server"`
	Database      DatabaseConfig      `mapstructure:"database"`
	JWT           JWTConfig           `mapstructure:"jwt"`
	Log           LogConfig           `mapstructure:"log"`
	RuleEngine    RuleEngineConfig    `mapstructure:"rule_engine"`
	ImageAnalysis ImageAnalysisConfig `mapstructure:"image_analysis"`
	SLA           SLAConfig           `mapstructure:"sla"`
}

type ServerConfig struct {
	Port int    `mapstructure:"port"`
	Mode string `mapstructure:"mode"`
}

type DatabaseConfig struct {
	Driver string `mapstructure:"driver"`
	DSN    string `mapstructure:"dsn"`
}

type JWTConfig struct {
	Secret  string `mapstructure:"secret"`
	Expires int    `mapstructure:"expires"`
}

type LogConfig struct {
	Level      string `mapstructure:"level"`
	Filename   string `mapstructure:"filename"`
	MaxSize    int    `mapstructure:"max_size"`
	MaxBackups int    `mapstructure:"max_backups"`
	MaxAge     int    `mapstructure:"max_age"`
}

type RuleEngineConfig struct {
	ServiceURL string `mapstructure:"service_url"`
}

type ImageAnalysisConfig struct {
	ServiceURL string `mapstructure:"service_url"`
}

type SLAConfig struct {
	EvidenceHours     float64 `mapstructure:"evidence_hours"`
	NegotiationHours  float64 `mapstructure:"negotiation_hours"`
	ArbitrationHours  float64 `mapstructure:"arbitration_hours"`
	WarningThreshold  float64 `mapstructure:"warning_threshold"`
	CriticalThreshold float64 `mapstructure:"critical_threshold"`
}

var AppConfig *Config

func Init() error {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath("./config")
	viper.AddConfigPath(".")

	viper.AutomaticEnv()

	if err := viper.ReadInConfig(); err != nil {
		return fmt.Errorf("failed to read config file: %w", err)
	}

	AppConfig = &Config{}
	if err := viper.Unmarshal(AppConfig); err != nil {
		return fmt.Errorf("failed to unmarshal config: %w", err)
	}

	if err := ensureDataDirectories(); err != nil {
		return err
	}

	return nil
}

func ensureDataDirectories() error {
	dirs := []string{
		"./data",
		"./logs",
		"./uploads/evidence",
		"./uploads/thumbnails",
	}

	for _, dir := range dirs {
		if _, err := os.Stat(dir); os.IsNotExist(err) {
			if err := os.MkdirAll(dir, 0755); err != nil {
				return fmt.Errorf("failed to create directory %s: %w", dir, err)
			}
		}
	}

	return nil
}
