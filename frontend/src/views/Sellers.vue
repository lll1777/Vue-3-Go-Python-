<template>
  <div class="sellers-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>商家管理</span>
          <div class="header-actions">
            <el-select v-model="filterScore" placeholder="服务分筛选" clearable style="width: 180px">
              <el-option label="90分以上（优秀）" value="excellent" />
              <el-option label="80-90分（良好）" value="good" />
              <el-option label="70-80分（一般）" value="average" />
              <el-option label="60-70分（及格）" value="pass" />
              <el-option label="60分以下（较差）" value="poor" />
            </el-select>
            <el-button type="primary" :icon="Refresh" @click="refreshData">
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-card class="stat-card excellent">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon :size="36"><Trophy /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ sellerStats.excellent }}</div>
                <div class="stat-label">优秀商家</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card good">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon :size="36"><Medal /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ sellerStats.good }}</div>
                <div class="stat-label">良好商家</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card average">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon :size="36"><User /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ sellerStats.poor }}</div>
                <div class="stat-label">需关注商家</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card info">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon :size="36"><TrendCharts /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ sellerStats.avgScore }}</div>
                <div class="stat-label">平均服务分</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-divider />

      <el-table :data="sellersList" v-loading="loading" row-key="id" style="width: 100%">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="shopName" label="店铺名称" min-width="180">
          <template #default="scope">
            <div class="seller-info">
              <el-avatar :size="40" :src="scope.row.shopLogo">
                <el-icon :size="20"><Shop /></el-icon>
              </el-avatar>
              <div class="seller-detail">
                <el-text class="shop-name">{{ scope.row.shopName }}</el-text>
                <el-text type="info" size="small">{{ scope.row.shopCode }}</el-text>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="serviceScore" label="服务分" width="150">
          <template #default="scope">
            <div class="score-column">
              <el-progress
                type="dashboard"
                :percentage="scope.row.serviceScore"
                :color="getScoreColor(scope.row.serviceScore)"
                :width="80"
              >
                <template #default="{ percentage }">
                  <span class="score-value">{{ percentage }}</span>
                </template>
              </el-progress>
              <el-tag :type="getScoreTag(scope.row.serviceScore)" size="small">
                {{ getScoreLevel(scope.row.serviceScore) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="disputeStats" label="纠纷统计" width="200">
          <template #default="scope">
            <div class="dispute-stats">
              <div class="stat-item">
                <span class="stat-label">总纠纷</span>
                <span class="stat-value">{{ scope.row.disputeCount }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">胜诉</span>
                <span class="stat-value success">{{ scope.row.disputeWins }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">败诉</span>
                <span class="stat-value danger">{{ scope.row.disputeLosses }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="winRate" label="胜诉率" width="100" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.winRate >= 70 ? 'success' : scope.row.winRate >= 50 ? 'warning' : 'danger'" size="small">
              {{ scope.row.winRate }}%
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="avgResolveHours" label="平均处理时长" width="120" align="center">
          <template #default="scope">
            <el-text :type="scope.row.avgResolveHours <= 12 ? 'success' : scope.row.avgResolveHours <= 24 ? 'primary' : 'danger'">
              {{ scope.row.avgResolveHours }}小时
            </el-text>
          </template>
        </el-table-column>
        <el-table-column prop="isVerified" label="认证状态" width="100" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.isVerified" type="success" size="small">已认证</el-tag>
            <el-tag v-else type="info" size="small">未认证</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="isPremium" label="会员等级" width="100" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.isPremium" type="warning" size="small">金牌卖家</el-tag>
            <el-tag v-else type="info" size="small">普通卖家</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="viewSeller(scope.row)">
              详情
            </el-button>
            <el-button type="primary" link @click="viewSellerHistory(scope.row)">
              历史
            </el-button>
            <el-button type="warning" link @click="adjustScore(scope.row)" v-if="scope.row.serviceScore < 70">
              扣分
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="showHistoryDialog" title="商家服务分历史" width="700px">
      <el-table :data="scoreHistory" style="width: 100%">
        <el-table-column prop="createdAt" label="时间" width="180" />
        <el-table-column prop="beforeScore" label="变更前" width="100" align="center">
          <template #default="scope">
            <el-text>{{ scope.row.beforeScore }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="afterScore" label="变更后" width="100" align="center">
          <template #default="scope">
            <el-text>{{ scope.row.afterScore }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="change" label="变动" width="100" align="center">
          <template #default="scope">
            <el-text :type="scope.row.change > 0 ? 'success' : 'danger'">
              {{ scope.row.change > 0 ? '+' : '' }}{{ scope.row.change }}
            </el-text>
          </template>
        </el-table-column>
        <el-table-column prop="reasonType" label="类型" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.change > 0 ? 'success' : 'danger'" size="small">
              {{ scope.row.reasonType }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="原因" min-width="150">
          <template #default="scope">
            <el-text type="info" size="small">{{ scope.row.reason }}</el-text>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <el-dialog v-model="showAdjustDialog" title="服务分调整" width="500px">
      <el-form :model="adjustForm" label-width="100px">
        <el-form-item label="当前分数">
          <el-text type="info">{{ currentSeller?.serviceScore }} 分</el-text>
        </el-form-item>
        <el-form-item label="调整类型">
          <el-radio-group v-model="adjustForm.type">
            <el-radio value="penalty">扣分</el-radio>
            <el-radio value="bonus">加分</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="调整分数">
          <el-input-number v-model="adjustForm.amount" :min="0" :max="20" :precision="1" />
          <el-text type="info" class="unit">分</el-text>
        </el-form-item>
        <el-form-item label="调整原因">
          <el-input v-model="adjustForm.reason" type="textarea" :rows="3" placeholder="请输入调整原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdjustDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAdjust" :loading="adjusting">确认调整</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Trophy, Medal, User, TrendCharts, Shop } from '@element-plus/icons-vue'

const loading = ref(false)
const adjusting = ref(false)
const filterScore = ref('')
const showHistoryDialog = ref(false)
const showAdjustDialog = ref(false)
const currentSeller = ref(null)

const sellerStats = ref({
  excellent: 12,
  good: 25,
  poor: 8,
  avgScore: 85.6
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 45
})

const adjustForm = reactive({
  type: 'penalty',
  amount: 2.0,
  reason: ''
})

const scoreHistory = ref([
  {
    id: 1,
    createdAt: '2026-04-28 14:30:00',
    beforeScore: 95.5,
    afterScore: 93.0,
    change: -2.5,
    reasonType: '仲裁败诉',
    reason: 'WT202604280001: 支持买家退款申请'
  },
  {
    id: 2,
    createdAt: '2026-04-25 10:15:00',
    beforeScore: 94.5,
    afterScore: 95.5,
    change: 1.0,
    reasonType: '快速响应',
    reason: '12小时内快速处理纠纷'
  },
  {
    id: 3,
    createdAt: '2026-04-20 16:45:00',
    beforeScore: 92.5,
    afterScore: 94.5,
    change: 2.0,
    reasonType: '仲裁胜诉',
    reason: 'WT202604200003: 驳回买家恶意投诉'
  },
  {
    id: 4,
    createdAt: '2026-04-15 09:20:00',
    beforeScore: 90.0,
    afterScore: 92.5,
    change: 2.5,
    reasonType: '连续胜诉',
    reason: '连续5次仲裁胜诉奖励'
  }
])

const sellersList = ref([
  {
    id: 1,
    shopCode: 'SH000001',
    shopName: '某某官方旗舰店',
    shopLogo: '',
    serviceScore: 92.5,
    disputeCount: 15,
    disputeWins: 12,
    disputeLosses: 3,
    winRate: 80,
    avgResolveHours: 12.5,
    isVerified: true,
    isPremium: true
  },
  {
    id: 2,
    shopCode: 'SH000002',
    shopName: '某某专营店',
    shopLogo: '',
    serviceScore: 88.3,
    disputeCount: 28,
    disputeWins: 20,
    disputeLosses: 8,
    winRate: 71,
    avgResolveHours: 18.2,
    isVerified: true,
    isPremium: true
  },
  {
    id: 3,
    shopCode: 'SH000003',
    shopName: '某某专卖店',
    shopLogo: '',
    serviceScore: 95.8,
    disputeCount: 8,
    disputeWins: 7,
    disputeLosses: 1,
    winRate: 88,
    avgResolveHours: 8.5,
    isVerified: true,
    isPremium: false
  },
  {
    id: 4,
    shopCode: 'SH000004',
    shopName: '某某小店',
    shopLogo: '',
    serviceScore: 75.2,
    disputeCount: 45,
    disputeWins: 28,
    disputeLosses: 17,
    winRate: 62,
    avgResolveHours: 32.5,
    isVerified: false,
    isPremium: false
  },
  {
    id: 5,
    shopCode: 'SH000005',
    shopName: '某某电商',
    shopLogo: '',
    serviceScore: 68.5,
    disputeCount: 62,
    disputeWins: 30,
    disputeLosses: 32,
    winRate: 48,
    avgResolveHours: 48.0,
    isVerified: false,
    isPremium: false
  }
])

const getScoreColor = (score) => {
  if (score >= 90) return '#67c23a'
  if (score >= 80) return '#409eff'
  if (score >= 70) return '#e6a23c'
  return '#f56c6c'
}

const getScoreTag = (score) => {
  if (score >= 90) return 'success'
  if (score >= 80) return 'primary'
  if (score >= 70) return 'warning'
  return 'danger'
}

const getScoreLevel = (score) => {
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 70) return '一般'
  if (score >= 60) return '及格'
  return '较差'
}

const refreshData = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    ElMessage.success('数据已刷新')
  }, 500)
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
}

const handleCurrentChange = (val) => {
  pagination.page = val
}

const viewSeller = (row) => {
  ElMessage.info(`查看商家详情: ${row.shopName}`)
}

const viewSellerHistory = (row) => {
  currentSeller.value = row
  showHistoryDialog.value = true
}

const adjustScore = (row) => {
  currentSeller.value = row
  adjustForm.amount = 2.0
  adjustForm.reason = ''
  adjustForm.type = 'penalty'
  showAdjustDialog.value = true
}

const confirmAdjust = async () => {
  if (!adjustForm.reason.trim()) {
    ElMessage.warning('请输入调整原因')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认${adjustForm.type === 'penalty' ? '扣除' : '增加'} ${adjustForm.amount} 分？`,
      '确认调整',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: adjustForm.type === 'penalty' ? 'warning' : 'success'
      }
    )

    adjusting.value = true
    setTimeout(() => {
      adjusting.value = false
      showAdjustDialog.value = false
      ElMessage.success(`服务分${adjustForm.type === 'penalty' ? '扣除' : '增加'}成功`)
    }, 1000)
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.sellers-page {
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
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  overflow: hidden;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  padding: 15px;
  border-radius: 8px;
}

.excellent .stat-icon { background: #f0f9eb; color: #67c23a; }
.good .stat-icon { background: #ecf5ff; color: #409eff; }
.average .stat-icon { background: #fdf6ec; color: #e6a23c; }
.info .stat-icon { background: #f4f4f5; color: #909399; }

.stat-info {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.seller-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.seller-detail {
  display: flex;
  flex-direction: column;
}

.shop-name {
  font-weight: bold;
  font-size: 14px;
}

.score-column {
  display: flex;
  align-items: center;
  gap: 10px;
}

.score-value {
  font-size: 18px;
  font-weight: bold;
}

.dispute-stats {
  display: flex;
  justify-content: space-between;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  font-size: 12px;
  color: #909399;
}

.stat-value {
  font-weight: bold;
}

.stat-value.success {
  color: #67c23a;
}

.stat-value.danger {
  color: #f56c6c;
}

.unit {
  margin-left: 8px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
