<template>
  <div class="sla-monitor">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>SLA时效监控</span>
          <div class="header-actions">
            <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width: 150px">
              <el-option label="举证期" value="evidence" />
              <el-option label="协商期" value="negotiation" />
              <el-option label="仲裁期" value="arbitration" />
            </el-select>
            <el-select v-model="filterSlaStatus" placeholder="SLA状态" clearable style="width: 150px">
              <el-option label="正常" value="normal" />
              <el-option label="预警" value="warning" />
              <el-option label="超时" value="timeout" />
            </el-select>
            <el-button type="primary" :icon="Refresh" @click="refreshData">
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-card class="stat-card normal">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon :size="36"><Clock /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ slaStats.normal }}</div>
                <div class="stat-label">正常处理中</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card warning">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon :size="36"><Warning /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ slaStats.warning }}</div>
                <div class="stat-label">即将超时</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card danger">
            <div class="stat-content">
              <div class="stat-icon">
                <el-icon :size="36"><Bell /></el-icon>
              </div>
              <div class="stat-info">
                <div class="stat-number">{{ slaStats.timeout }}</div>
                <div class="stat-label">已超时</div>
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
                <div class="stat-number">{{ slaStats.avgHours }}h</div>
                <div class="stat-label">平均处理时长</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-divider />

      <el-table :data="slaList" v-loading="loading" style="width: 100%">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="ticketNo" label="工单编号" width="180" />
        <el-table-column prop="title" label="工单标题" min-width="200" />
        <el-table-column prop="stage" label="当前阶段" width="100">
          <template #default="scope">
            <el-tag :type="getStageTag(scope.row.stage)" size="small">
              {{ getStageText(scope.row.stage) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="slaStatus" label="SLA状态" width="100">
          <template #default="scope">
            <el-tag :type="getSlaTag(scope.row.slaStatus)" size="small">
              {{ getSlaStatusText(scope.row.slaStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remainingHours" label="剩余时间" width="150">
          <template #default="scope">
            <div class="remaining-column">
              <el-progress
                :percentage="scope.row.percentage"
                :color="getProgressColor(scope.row.percentage)"
                :stroke-width="10"
              />
              <el-text :type="getRemainingTextType(scope.row)" size="small">
                {{ formatRemaining(scope.row.remainingHours) }}
              </el-text>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="slaEndTime" label="截止时间" width="180" />
        <el-table-column prop="sellerName" label="商家" width="150">
          <template #default="scope">
            <div class="seller-info">
              <el-text>{{ scope.row.sellerName }}</el-text>
              <el-tag :type="getScoreTag(scope.row.sellerScore)" size="small">
                {{ scope.row.sellerScore }}分
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="viewTicket(scope.row.ticketId)">
              查看
            </el-button>
            <el-button type="warning" link @click="handleAlert(scope.row)" v-if="scope.row.slaStatus !== 'normal'">
              提醒
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Clock, Warning, Bell, TrendCharts } from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const filterStatus = ref('')
const filterSlaStatus = ref('')

const slaStats = ref({
  normal: 15,
  warning: 8,
  timeout: 3,
  avgHours: 18.5
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 100
})

const slaList = ref([
  {
    ticketId: 1,
    ticketNo: 'WT202604290001',
    title: '申请仅退款 - 商品质量问题',
    stage: 'negotiation',
    slaStatus: 'normal',
    remainingHours: 12.5,
    percentage: 48,
    slaEndTime: '2026-04-30 22:30:00',
    sellerName: '某某官方旗舰店',
    sellerScore: 92.5
  },
  {
    ticketId: 2,
    ticketNo: 'WT202604290002',
    title: '退货退款申请',
    stage: 'evidence',
    slaStatus: 'warning',
    remainingHours: 4.5,
    percentage: 82,
    slaEndTime: '2026-04-30 14:15:00',
    sellerName: '某某专营店',
    sellerScore: 88.3
  },
  {
    ticketId: 3,
    ticketNo: 'WT202604290003',
    title: '虚假宣传投诉',
    stage: 'arbitration',
    slaStatus: 'timeout',
    remainingHours: -2.3,
    percentage: 108,
    slaEndTime: '2026-04-30 08:00:00',
    sellerName: '某某小店',
    sellerScore: 72.1
  },
  {
    ticketId: 4,
    ticketNo: 'WT202604290004',
    title: '延迟发货投诉',
    stage: 'negotiation',
    slaStatus: 'warning',
    remainingHours: 3.2,
    percentage: 87,
    slaEndTime: '2026-04-30 12:45:00',
    sellerName: '某某电商',
    sellerScore: 68.5
  },
  {
    ticketId: 5,
    ticketNo: 'WT202604290005',
    title: '客服态度恶劣投诉',
    stage: 'evidence',
    slaStatus: 'normal',
    remainingHours: 18.75,
    percentage: 22,
    slaEndTime: '2026-05-01 04:30:00',
    sellerName: '某某官方旗舰店',
    sellerScore: 92.5
  }
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

const getSlaStatusText = (status) => {
  const map = {
    normal: '正常',
    warning: '预警',
    timeout: '超时'
  }
  return map[status] || status
}

const getSlaTag = (status) => {
  const map = {
    normal: 'success',
    warning: 'warning',
    timeout: 'danger'
  }
  return map[status] || 'info'
}

const getProgressColor = (percentage) => {
  if (percentage > 100) return '#f56c6c'
  if (percentage > 80) return '#e6a23c'
  return '#67c23a'
}

const getRemainingTextType = (row) => {
  if (row.remainingHours < 0) return 'danger'
  if (row.remainingHours < 6) return 'warning'
  return 'info'
}

const getScoreTag = (score) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'primary'
  return 'danger'
}

const formatRemaining = (hours) => {
  if (hours < 0) {
    return `已超时 ${Math.abs(hours).toFixed(1)} 小时`
  }
  if (hours < 1) {
    return `${Math.floor(hours * 60)} 分钟`
  }
  return `${hours.toFixed(1)} 小时`
}

const viewTicket = (id) => {
  router.push(`/tickets/${id}`)
}

const handleAlert = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认给商家 "${row.sellerName}" 发送SLA超时提醒？`,
      '发送提醒',
      {
        confirmButtonText: '确认发送',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    ElMessage.success('提醒已发送')
  } catch {
    // 用户取消
  }
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

onMounted(() => {
  // 加载数据
})
</script>

<style scoped>
.sla-monitor {
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

.normal .stat-icon { background: #f0f9eb; color: #67c23a; }
.warning .stat-icon { background: #fdf6ec; color: #e6a23c; }
.danger .stat-icon { background: #fef0f0; color: #f56c6c; }
.info .stat-icon { background: #ecf5ff; color: #409eff; }

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

.remaining-column {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.seller-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
