<template>
  <div class="statistics-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据统计</span>
          <div class="header-actions">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
            />
            <el-select v-model="filterPeriod" placeholder="时间范围" style="width: 120px">
              <el-option label="今日" value="today" />
              <el-option label="本周" value="week" />
              <el-option label="本月" value="month" />
              <el-option label="近30天" value="30days" />
              <el-option label="近90天" value="90days" />
            </el-select>
            <el-button type="primary" :icon="Search" @click="loadData">
              查询
            </el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="20" class="overview-row">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-header">
              <el-icon :size="28" color="#409eff"><Document /></el-icon>
              <span class="stat-title">总工单</span>
            </div>
            <div class="stat-value">{{ overviewStats.totalTickets }}</div>
            <div class="stat-trend" :class="overviewStats.totalTrend >= 0 ? 'up' : 'down'">
              <el-icon><TrendCharts /></el-icon>
              <span>{{ Math.abs(overviewStats.totalTrend) }}%</span>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-header">
              <el-icon :size="28" color="#67c23a"><CircleCheck /></el-icon>
              <span class="stat-title">已解决</span>
            </div>
            <div class="stat-value">{{ overviewStats.resolvedTickets }}</div>
            <div class="stat-trend" :class="overviewStats.resolvedTrend >= 0 ? 'up' : 'down'">
              <el-icon><TrendCharts /></el-icon>
              <span>{{ Math.abs(overviewStats.resolvedTrend) }}%</span>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-header">
              <el-icon :size="28" color="#e6a23c"><Timer /></el-icon>
              <span class="stat-title">处理中</span>
            </div>
            <div class="stat-value">{{ overviewStats.processingTickets }}</div>
            <div class="stat-trend" :class="overviewStats.processingTrend >= 0 ? 'up' : 'down'">
              <el-icon><TrendCharts /></el-icon>
              <span>{{ Math.abs(overviewStats.processingTrend) }}%</span>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-header">
              <el-icon :size="28" color="#f56c6c"><Bell /></el-icon>
              <span class="stat-title">SLA超时</span>
            </div>
            <div class="stat-value">{{ overviewStats.slaTimeouts }}</div>
            <div class="stat-trend" :class="overviewStats.slaTrend >= 0 ? 'up' : 'down'">
              <el-icon><TrendCharts /></el-icon>
              <span>{{ Math.abs(overviewStats.slaTrend) }}%</span>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-divider content-position="left">关键指标</el-divider>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-card>
            <template #header>
              <span>工单类型分布</span>
            </template>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="仅退款">
                <div class="distribution-item">
                  <el-progress :percentage="typeDistribution.refund" :stroke-width="10" />
                  <span class="count">{{ typeDistribution.refundCount }} 单</span>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="退货退款">
                <div class="distribution-item">
                  <el-progress :percentage="typeDistribution.return" :stroke-width="10" color="#67c23a" />
                  <span class="count">{{ typeDistribution.returnCount }} 单</span>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="投诉">
                <div class="distribution-item">
                  <el-progress :percentage="typeDistribution.complaint" :stroke-width="10" color="#e6a23c" />
                  <span class="count">{{ typeDistribution.complaintCount }} 单</span>
                </div>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card>
            <template #header>
              <span>问题分类分布</span>
            </template>
            <el-table :data="categoryDistribution" size="small">
              <el-table-column prop="category" label="分类" />
              <el-table-column prop="count" label="数量" align="center" />
              <el-table-column prop="percentage" label="占比" align="center">
                <template #default="scope">
                  <el-tag :type="scope.row.percentage >= 30 ? 'danger' : scope.row.percentage >= 20 ? 'warning' : 'info'" size="small">
                    {{ scope.row.percentage }}%
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card>
            <template #header>
              <span>处理效率指标</span>
            </template>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="平均处理时长">
                <el-text type="primary" size="large" class="highlight-value">
                  {{ efficiencyMetrics.avgResolveHours }} 小时
                </el-text>
              </el-descriptions-item>
              <el-descriptions-item label="结案率">
                <el-text type="success" size="large" class="highlight-value">
                  {{ efficiencyMetrics.resolutionRate }}%
                </el-text>
              </el-descriptions-item>
              <el-descriptions-item label="买家胜诉率">
                <el-text type="warning" size="large" class="highlight-value">
                  {{ efficiencyMetrics.buyerWinRate }}%
                </el-text>
              </el-descriptions-item>
              <el-descriptions-item label="自动判定准确率">
                <el-text type="primary" size="large" class="highlight-value">
                  {{ efficiencyMetrics.autoDecisionAccuracy }}%
                </el-text>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
      </el-row>

      <el-divider content-position="left">SLA监控统计</el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>各阶段SLA超时情况</span>
            </template>
            <el-table :data="slaStageStats" size="small">
              <el-table-column prop="stage" label="阶段">
                <template #default="scope">
                  <el-tag :type="getStageTag(scope.row.stage)">{{ getStageText(scope.row.stage) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="total" label="总工单" align="center" />
              <el-table-column prop="normal" label="正常处理" align="center">
                <template #default="scope">
                  <el-text type="success">{{ scope.row.normal }}</el-text>
                </template>
              </el-table-column>
              <el-table-column prop="warning" label="预警" align="center">
                <template #default="scope">
                  <el-text type="warning">{{ scope.row.warning }}</el-text>
                </template>
              </el-table-column>
              <el-table-column prop="timeout" label="超时" align="center">
                <template #default="scope">
                  <el-text type="danger">{{ scope.row.timeout }}</el-text>
                </template>
              </el-table-column>
              <el-table-column prop="timeoutRate" label="超时率" align="center">
                <template #default="scope">
                  <el-progress
                    :percentage="scope.row.timeoutRate"
                    :color="scope.row.timeoutRate > 20 ? '#f56c6c' : scope.row.timeoutRate > 10 ? '#e6a23c' : '#67c23a'"
                    :stroke-width="8"
                  />
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card>
            <template #header>
              <span>商家服务分分布</span>
            </template>
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="优秀商家(≥90分)">
                <div class="score-distribution">
                  <el-text type="success" size="large" class="highlight-value">
                    {{ sellerScoreDistribution.excellent }}
                  </el-text>
                  <span class="unit">家</span>
                  <el-tag type="success" size="small">{{ sellerScoreDistribution.excellentPercent }}%</el-tag>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="良好商家(80-89分)">
                <div class="score-distribution">
                  <el-text type="primary" size="large" class="highlight-value">
                    {{ sellerScoreDistribution.good }}
                  </el-text>
                  <span class="unit">家</span>
                  <el-tag type="primary" size="small">{{ sellerScoreDistribution.goodPercent }}%</el-tag>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="一般商家(70-79分)">
                <div class="score-distribution">
                  <el-text type="warning" size="large" class="highlight-value">
                    {{ sellerScoreDistribution.average }}
                  </el-text>
                  <span class="unit">家</span>
                  <el-tag type="warning" size="small">{{ sellerScoreDistribution.averagePercent }}%</el-tag>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="需关注商家(<70分)">
                <div class="score-distribution">
                  <el-text type="danger" size="large" class="highlight-value">
                    {{ sellerScoreDistribution.poor }}
                  </el-text>
                  <span class="unit">家</span>
                  <el-tag type="danger" size="small">{{ sellerScoreDistribution.poorPercent }}%</el-tag>
                </div>
              </el-descriptions-item>
            </el-descriptions>

            <el-divider />

            <div class="score-summary">
              <div class="summary-item">
                <span class="summary-label">平均服务分</span>
                <span class="summary-value">{{ sellerScoreDistribution.avgScore }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">总商家数</span>
                <span class="summary-value">{{ sellerScoreDistribution.total }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">金牌卖家</span>
                <span class="summary-value">{{ sellerScoreDistribution.premium }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-divider content-position="left">图片分析统计</el-divider>

      <el-row :gutter="20">
        <el-col :span="24">
          <el-card>
            <template #header>
              <span>虚假宣传检测统计</span>
            </template>
            <el-table :data="imageAnalysisStats" size="small">
              <el-table-column prop="period" label="时间周期" width="120" />
              <el-table-column prop="totalImages" label="分析图片数" align="center" />
              <el-table-column prop="falseClaimDetected" label="检测到虚假宣传" align="center">
                <template #default="scope">
                  <el-tag type="danger" size="small">{{ scope.row.falseClaimDetected }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="qualityIssues" label="质量问题" align="center">
                <template #default="scope">
                  <el-tag type="warning" size="small">{{ scope.row.qualityIssues }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="usedProducts" label="二手商品" align="center">
                <template #default="scope">
                  <el-tag type="danger" size="small">{{ scope.row.usedProducts }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="textExtracted" label="提取文本数" align="center" />
              <el-table-column prop="detectionRate" label="检测率" align="center">
                <template #default="scope">
                  <el-text type="primary">{{ scope.row.detectionRate }}%</el-text>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import {
  Document, CircleCheck, Timer, Bell, TrendCharts, Search
} from '@element-plus/icons-vue'

const dateRange = ref([])
const filterPeriod = ref('30days')

const overviewStats = ref({
  totalTickets: 1256,
  totalTrend: 12.5,
  resolvedTickets: 987,
  resolvedTrend: 18.2,
  processingTickets: 245,
  processingTrend: -5.3,
  slaTimeouts: 24,
  slaTrend: -10.5
})

const typeDistribution = ref({
  refund: 45,
  refundCount: 565,
  return: 35,
  returnCount: 440,
  complaint: 20,
  complaintCount: 251
})

const categoryDistribution = ref([
  { category: '质量问题', count: 456, percentage: 36.3 },
  { category: '虚假宣传', count: 312, percentage: 24.8 },
  { category: '物流问题', count: 234, percentage: 18.6 },
  { category: '服务问题', count: 156, percentage: 12.4 },
  { category: '其他', count: 98, percentage: 7.8 }
])

const efficiencyMetrics = ref({
  avgResolveHours: 18.5,
  resolutionRate: 78.6,
  buyerWinRate: 65.2,
  autoDecisionAccuracy: 82.3
})

const slaStageStats = ref([
  { stage: 'evidence', total: 85, normal: 68, warning: 12, timeout: 5, timeoutRate: 5.9 },
  { stage: 'negotiation', total: 120, normal: 85, warning: 22, timeout: 13, timeoutRate: 10.8 },
  { stage: 'arbitration', total: 45, normal: 28, warning: 10, timeout: 7, timeoutRate: 15.6 }
])

const sellerScoreDistribution = ref({
  excellent: 45,
  excellentPercent: 28.1,
  good: 68,
  goodPercent: 42.5,
  average: 28,
  averagePercent: 17.5,
  poor: 19,
  poorPercent: 11.9,
  avgScore: 83.6,
  total: 160,
  premium: 32
})

const imageAnalysisStats = ref([
  { period: '今日', totalImages: 45, falseClaimDetected: 8, qualityIssues: 12, usedProducts: 3, textExtracted: 38, detectionRate: 51.1 },
  { period: '本周', totalImages: 285, falseClaimDetected: 42, qualityIssues: 68, usedProducts: 18, textExtracted: 235, detectionRate: 44.9 },
  { period: '本月', totalImages: 1256, falseClaimDetected: 185, qualityIssues: 298, usedProducts: 76, textExtracted: 1025, detectionRate: 44.5 }
])

const getStageText = (stage) => {
  const map = {
    evidence: '举证期',
    negotiation: '协商期',
    arbitration: '仲裁期'
  }
  return map[stage] || stage
}

const getStageTag = (stage) => {
  const map = {
    evidence: 'warning',
    negotiation: 'primary',
    arbitration: 'danger'
  }
  return map[stage] || 'info'
}

const loadData = () => {
  // 模拟加载数据
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.statistics-page {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.overview-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.stat-title {
  font-size: 14px;
  color: #606266;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 10px;
  font-size: 14px;
}

.stat-trend.up {
  color: #67c23a;
}

.stat-trend.down {
  color: #f56c6c;
}

.distribution-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.count {
  font-size: 12px;
  color: #909399;
}

.highlight-value {
  font-weight: bold;
}

.score-distribution {
  display: flex;
  align-items: center;
  gap: 8px;
}

.unit {
  font-size: 12px;
  color: #909399;
}

.score-summary {
  display: flex;
  justify-content: space-around;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.summary-label {
  font-size: 12px;
  color: #909399;
}

.summary-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}
</style>
