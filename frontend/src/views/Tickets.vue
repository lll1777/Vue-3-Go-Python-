<template>
  <div class="tickets-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>工单列表</span>
          <div class="header-actions">
            <el-button type="primary" :icon="Plus" @click="goToCreate">
              新建工单
            </el-button>
          </div>
        </div>
      </template>

      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="工单编号">
          <el-input v-model="searchForm.ticketNo" placeholder="请输入工单编号" clearable />
        </el-form-item>
        <el-form-item label="订单号">
          <el-input v-model="searchForm.orderNo" placeholder="请输入订单号" clearable />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="searchForm.type" placeholder="全部类型" clearable>
            <el-option label="仅退款" value="refund" />
            <el-option label="退货退款" value="return" />
            <el-option label="投诉" value="complaint" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable>
            <el-option label="待举证" value="pending" />
            <el-option label="举证期" value="evidence" />
            <el-option label="协商中" value="negotiation" />
            <el-option label="平台介入" value="platform" />
            <el-option label="仲裁中" value="arbitration" />
            <el-option label="执行中" value="executing" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="SLA状态">
          <el-select v-model="searchForm.slaStatus" placeholder="全部" clearable>
            <el-option label="正常" value="normal" />
            <el-option label="预警" value="warning" />
            <el-option label="超时" value="timeout" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="ticketList" v-loading="loading" style="width: 100%">
        <el-table-column prop="ticketNo" label="工单编号" width="180" fixed />
        <el-table-column prop="orderNo" label="订单号" width="150" />
        <el-table-column prop="buyerName" label="买家" width="100" />
        <el-table-column prop="sellerName" label="商家" width="150" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="scope">
            <el-tag :type="getTypeTag(scope.row.type)" size="small">
              {{ getTypeText(scope.row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusTag(scope.row.status)" size="small">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="slaRemaining" label="SLA剩余时间" width="150">
          <template #default="scope">
            <div class="sla-column">
              <el-progress 
                :percentage="scope.row.slaPercentage" 
                :color="getSlaProgressColor(scope.row.slaPercentage)"
                :stroke-width="8"
              />
              <el-text :type="getSlaTextType(scope.row.slaRemaining)" size="small">
                {{ scope.row.slaRemaining }}
              </el-text>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="autoDecision" label="自动判定" width="120">
          <template #default="scope">
            <template v-if="scope.row.autoDecision">
              <el-tag :type="getDecisionTag(scope.row.autoDecision)" size="small">
                {{ getDecisionText(scope.row.autoDecision) }}
              </el-tag>
            </template>
            <el-tag type="info" size="small" v-else>待判定</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="viewTicket(scope.row.id)">
              查看
            </el-button>
            <el-button type="success" link @click="goToChat(scope.row.id)" v-if="scope.row.status === 'negotiation'">
              协商
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
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)

const searchForm = reactive({
  ticketNo: '',
  orderNo: '',
  type: '',
  status: '',
  slaStatus: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 100
})

const ticketList = ref([
  {
    id: 1,
    ticketNo: 'WT202604290001',
    orderNo: 'ORD20260428001',
    buyerName: '张三',
    sellerName: '某某官方旗舰店',
    type: 'refund',
    status: 'evidence',
    slaRemaining: '12小时30分',
    slaPercentage: 40,
    autoDecision: 'refund',
    createTime: '2026-04-29 10:30:00'
  },
  {
    id: 2,
    ticketNo: 'WT202604290002',
    orderNo: 'ORD20260428002',
    buyerName: '李四',
    sellerName: '某某专营店',
    type: 'return',
    status: 'negotiation',
    slaRemaining: '24小时',
    slaPercentage: 70,
    autoDecision: null,
    createTime: '2026-04-29 09:15:00'
  },
  {
    id: 3,
    ticketNo: 'WT202604290003',
    orderNo: 'ORD20260428003',
    buyerName: '王五',
    sellerName: '某某专卖店',
    type: 'complaint',
    status: 'arbitration',
    slaRemaining: '5小时',
    slaPercentage: 15,
    autoDecision: 'seller_responsible',
    createTime: '2026-04-28 14:20:00'
  },
  {
    id: 4,
    ticketNo: 'WT202604290004',
    orderNo: 'ORD20260428004',
    buyerName: '赵六',
    sellerName: '某某小店',
    type: 'refund',
    status: 'executing',
    slaRemaining: '-2小时',
    slaPercentage: 110,
    autoDecision: 'refund',
    createTime: '2026-04-27 16:45:00'
  },
  {
    id: 5,
    ticketNo: 'WT202604290005',
    orderNo: 'ORD20260428005',
    buyerName: '钱七',
    sellerName: '某某电商',
    type: 'return',
    status: 'closed',
    slaRemaining: '已完成',
    slaPercentage: 0,
    autoDecision: 'return',
    createTime: '2026-04-26 11:30:00'
  }
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
    pending: '待举证',
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
    pending: 'info',
    evidence: 'warning',
    negotiation: 'primary',
    platform: 'danger',
    arbitration: 'danger',
    executing: 'info',
    closed: 'success'
  }
  return map[status] || 'info'
}

const getSlaProgressColor = (percentage) => {
  if (percentage > 100) return '#f56c6c'
  if (percentage > 80) return '#e6a23c'
  return '#67c23a'
}

const getSlaTextType = (remaining) => {
  if (remaining.startsWith('-') || remaining === '超时') return 'danger'
  return 'info'
}

const getDecisionText = (decision) => {
  const map = {
    refund: '支持退款',
    return: '支持退货退款',
    reject: '驳回申请',
    seller_responsible: '商家责任',
    buyer_responsible: '买家责任',
    partial_refund: '部分退款'
  }
  return map[decision] || decision
}

const getDecisionTag = (decision) => {
  const map = {
    refund: 'success',
    return: 'success',
    reject: 'danger',
    seller_responsible: 'danger',
    buyer_responsible: 'warning',
    partial_refund: 'primary'
  }
  return map[decision] || 'info'
}

const handleSearch = () => {
  console.log('搜索:', searchForm)
  // 实际调用API
}

const handleReset = () => {
  Object.assign(searchForm, {
    ticketNo: '',
    orderNo: '',
    type: '',
    status: '',
    slaStatus: ''
  })
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
}

const handleCurrentChange = (val) => {
  pagination.page = val
}

const goToCreate = () => router.push('/create')
const viewTicket = (id) => router.push(`/tickets/${id}`)
const goToChat = (id) => router.push(`/chat?ticketId=${id}`)

onMounted(() => {
  // 加载数据
})
</script>

<style scoped>
.tickets-page {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.sla-column {
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
