<template>
  <div class="dashboard">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card pending">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.pending }}</div>
              <div class="stat-label">待处理工单</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card processing">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><ChatDotRound /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.processing }}</div>
              <div class="stat-label">协商中工单</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card arbitration">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><ScaleToBalance /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.arbitration }}</div>
              <div class="stat-label">仲裁中工单</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card warning">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="40"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-number">{{ stats.slaWarning }}</div>
              <div class="stat-label">SLA预警</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="content-row">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近工单</span>
              <el-button type="primary" link @click="goToTickets">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentTickets" style="width: 100%">
            <el-table-column prop="ticketNo" label="工单编号" width="180" />
            <el-table-column prop="orderNo" label="订单号" width="150" />
            <el-table-column prop="type" label="类型" width="100">
              <template #default="scope">
                <el-tag :type="getTypeTag(scope.row.type)">
                  {{ getTypeText(scope.row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="scope">
                <el-tag :type="getStatusTag(scope.row.status)">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="slaRemaining" label="SLA剩余" width="130">
              <template #default="scope">
                <el-tag :type="getSlaTag(scope.row.slaRemaining)">
                  {{ scope.row.slaRemaining }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right">
              <template #default="scope">
                <el-button type="primary" link @click="viewTicket(scope.row.id)">
                  查看
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快捷操作</span>
            </div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" size="large" :icon="Plus" @click="goToCreate">
              创建维权工单
            </el-button>
            <el-button type="success" size="large" :icon="ChatDotRound" @click="goToChat">
              协商聊天
            </el-button>
            <el-button type="warning" size="large" :icon="View" @click="goToCases">
              案例库
            </el-button>
            <el-button type="info" size="large" :icon="DataAnalysis" @click="goToStatistics" v-if="showAdminFeatures">
              数据统计
            </el-button>
          </div>
        </el-card>

        <el-card class="seller-card" v-if="userStore.currentUser?.role === 'admin'">
          <template #header>
            <div class="card-header">
              <span>商家服务分排行</span>
            </div>
          </template>
          <el-table :data="sellerRanking" size="small">
            <el-table-column prop="rank" label="排名" width="60">
              <template #default="scope">
                <el-tag :type="scope.$index < 3 ? 'danger' : 'info'" size="small">
                  {{ scope.row.rank }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="sellerName" label="商家" />
            <el-table-column prop="score" label="服务分" width="80">
              <template #default="scope">
                <el-text :type="getScoreType(scope.row.score)">
                  {{ scope.row.score }}
                </el-text>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Plus, ChatDotRound, View, DataAnalysis } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const showAdminFeatures = computed(() => {
  const role = userStore.currentUser?.role
  return role === 'admin' || role === 'arbitrator'
})

const stats = ref({
  pending: 12,
  processing: 8,
  arbitration: 5,
  slaWarning: 3
})

const recentTickets = ref([
  {
    id: 1,
    ticketNo: 'WT202604290001',
    orderNo: 'ORD20260428001',
    type: 'refund',
    status: 'evidence',
    slaRemaining: '12小时30分'
  },
  {
    id: 2,
    ticketNo: 'WT202604290002',
    orderNo: 'ORD20260428002',
    type: 'return',
    status: 'negotiation',
    slaRemaining: '24小时'
  },
  {
    id: 3,
    ticketNo: 'WT202604290003',
    orderNo: 'ORD20260428003',
    type: 'complaint',
    status: 'arbitration',
    slaRemaining: '5小时'
  },
  {
    id: 4,
    ticketNo: 'WT202604290004',
    orderNo: 'ORD20260428004',
    type: 'refund',
    status: 'executing',
    slaRemaining: '-2小时'
  }
])

const sellerRanking = ref([
  { rank: 1, sellerName: '某某官方旗舰店', score: 95.8 },
  { rank: 2, sellerName: '某某专营店', score: 92.3 },
  { rank: 3, sellerName: '某某专卖店', score: 88.7 },
  { rank: 4, sellerName: '某某小店', score: 75.2 },
  { rank: 5, sellerName: '某某电商', score: 68.5 }
])

const getTypeText = (type) => {
  const map = { refund: '仅退款', return: '退货退款', complaint: '投诉' }
  return map[type] || type
}

const getTypeTag = (type) => {
  const map = { refund: 'primary', return: 'success', complaint: 'warning' }
  return map[type] || 'info'
}

const getStatusText = (status) => {
  const map = {
    evidence: '举证期',
    negotiation: '协商中',
    platform: '平台介入',
    arbitration: '仲裁中',
    executing: '执行中',
    closed: '已关闭'
  }
  return map[status] || status
}

const getStatusTag = (status) => {
  const map = {
    evidence: 'warning',
    negotiation: 'primary',
    platform: 'danger',
    arbitration: 'danger',
    executing: 'info',
    closed: 'success'
  }
  return map[status] || 'info'
}

const getSlaTag = (remaining) => {
  if (remaining.startsWith('-')) return 'danger'
  const hours = parseInt(remaining)
  if (hours < 6) return 'danger'
  if (hours < 12) return 'warning'
  return 'success'
}

const getScoreType = (score) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'primary'
  return 'danger'
}

const goToTickets = () => router.push('/tickets')
const goToCreate = () => router.push('/create')
const goToChat = () => router.push('/chat')
const goToCases = () => router.push('/cases')
const goToStatistics = () => router.push('/statistics')
const viewTicket = (id) => router.push(`/tickets/${id}`)

onMounted(() => {
  // 加载数据
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-3px);
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

.pending .stat-icon { background: #ecf5ff; color: #409eff; }
.processing .stat-icon { background: #f0f9eb; color: #67c23a; }
.arbitration .stat-icon { background: #fdf6ec; color: #e6a23c; }
.warning .stat-icon { background: #fef0f0; color: #f56c6c; }

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

.content-row {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.quick-actions .el-button {
  width: 100%;
  justify-content: center;
}

.seller-card {
  margin-top: 20px;
}
</style>
