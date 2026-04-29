<template>
  <div class="ticket-detail">
    <el-row :gutter="20">
      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <div class="title-section">
                <el-tag :type="getStatusTag(ticket.status)" size="large">
                  {{ getStatusText(ticket.status) }}
                </el-tag>
                <el-text class="ticket-title">{{ ticket.title }}</el-text>
              </div>
              <div class="ticket-no">
                工单编号: {{ ticket.ticketNo }}
              </div>
            </div>
          </template>

          <div class="ticket-info">
            <el-descriptions :column="3" border>
              <el-descriptions-item label="订单号">{{ ticket.orderNo }}</el-descriptions-item>
              <el-descriptions-item label="商品">{{ ticket.productName }}</el-descriptions-item>
              <el-descriptions-item label="类型">
                <el-tag :type="getTypeTag(ticket.type)">{{ getTypeText(ticket.type) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="申请金额">{{ ticket.amount }} 元</el-descriptions-item>
              <el-descriptions-item label="申请时间">{{ ticket.createTime }}</el-descriptions-item>
              <el-descriptions-item label="关联商家">{{ ticket.sellerName }}</el-descriptions-item>
            </el-descriptions>
          </div>

          <el-divider />

          <div class="description-section">
            <h4>问题描述</h4>
            <el-text>{{ ticket.description }}</el-text>
          </div>

          <el-divider />

          <div class="evidence-section">
            <h4>举证材料</h4>
            <el-upload
              v-model:file-list="evidenceFiles"
              :auto-upload="false"
              list-type="picture-card"
              :on-preview="handlePreview"
              :on-change="handleEvidenceChange"
            >
              <el-icon><Plus /></el-icon>
              <template #tip>
                <div class="el-upload__tip">
                  支持jpg/png/gif格式，可上传图片证据
                </div>
              </template>
            </el-upload>
            <el-button type="primary" :icon="Upload" class="upload-btn" @click="uploadEvidence">
              上传证据
            </el-button>
          </div>

          <el-divider />

          <div class="chat-section">
            <h4>协商聊天</h4>
            <div class="chat-container" ref="chatContainer">
              <div v-for="msg in messages" :key="msg.id" :class="['chat-message', msg.type]">
                <div class="message-header">
                  <el-tag :type="msg.fromType === 'buyer' ? 'primary' : 'success'" size="small">
                    {{ getFromText(msg.fromType) }}
                  </el-tag>
                  <el-text type="info" size="small">{{ msg.time }}</el-text>
                </div>
                <div class="message-content">{{ msg.content }}</div>
                <div v-if="msg.evidence" class="message-evidence">
                  <el-text type="primary" size="small">
                    <el-icon><Paperclip /></el-icon> {{ msg.evidence }}
                  </el-text>
                </div>
              </div>
            </div>
            <div class="chat-input">
              <el-input
                v-model="newMessage"
                type="textarea"
                :rows="2"
                placeholder="输入消息..."
                @keyup.enter.ctrl="sendMessage"
              />
              <div class="chat-actions">
                <el-button :icon="Picture" @click="showUpload = true">
                  上传图片
                </el-button>
                <el-button type="primary" @click="sendMessage">
                  发送
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <span>SLA时效监控</span>
          </template>
          <div class="sla-panel">
            <div class="sla-item">
              <el-text type="info">当前阶段</el-text>
              <el-tag :type="getStatusTag(ticket.status)">{{ getStatusText(ticket.status) }}</el-tag>
            </div>
            <div class="sla-item">
              <el-text type="info">剩余时间</el-text>
              <el-text :type="getSlaType(ticket.slaRemaining)" size="large" class="sla-time">
                {{ ticket.slaRemaining }}
              </el-text>
            </div>
            <el-progress 
              :percentage="ticket.slaPercentage" 
              :color="getSlaProgressColor(ticket.slaPercentage)"
              :stroke-width="10"
            />
            <div class="sla-warnings" v-if="ticket.slaPercentage > 80">
              <el-alert
                :title="ticket.slaPercentage > 100 ? '已超时' : '即将超时'"
                :type="ticket.slaPercentage > 100 ? 'error' : 'warning'"
                :closable="false"
                show-icon
              />
            </div>
          </div>
        </el-card>

        <el-card class="auto-decision-card">
          <template #header>
            <span>自动判定结果</span>
          </template>
          <div class="decision-panel">
            <div v-if="ticket.autoDecision" class="decision-result">
              <el-alert
                :title="getDecisionText(ticket.autoDecision)"
                :type="getDecisionAlertType(ticket.autoDecision)"
                :closable="false"
                show-icon
              >
                <template #default>
                  <div class="decision-details">
                    <p><strong>置信度:</strong> {{ ticket.decisionConfidence }}%</p>
                    <p><strong>判定依据:</strong></p>
                    <ul>
                      <li v-for="(rule, idx) in ticket.decisionRules" :key="idx">{{ rule }}</li>
                    </ul>
                  </div>
                </template>
              </el-alert>
              <div class="decision-actions">
                <el-button type="success" @click="acceptDecision">
                  接受判定
                </el-button>
                <el-button type="warning" @click="escalate">
                  申请平台介入
                </el-button>
              </div>
            </div>
            <div v-else class="decision-pending">
              <el-text type="info">等待更多证据进行自动判定...</el-text>
              <el-progress type="dashboard" :percentage="60" />
            </div>
          </div>
        </el-card>

        <el-card class="similar-cases-card">
          <template #header>
            <span>相似案例推荐</span>
          </template>
          <div class="cases-panel">
            <el-timeline>
              <el-timeline-item
                v-for="(item, idx) in similarCases"
                :key="idx"
                :type="item.type"
                :timestamp="item.time"
                placement="top"
              >
                <el-card shadow="hover" class="case-card" @click="viewCase(item.id)">
                  <div class="case-title">{{ item.title }}</div>
                  <div class="case-info">
                    <el-tag size="small">{{ item.decision }}</el-tag>
                    <el-text type="info" size="small">相似度: {{ item.similarity }}%</el-text>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>

        <el-card class="seller-score-card">
          <template #header>
            <span>商家服务分</span>
          </template>
          <div class="score-panel">
            <el-progress
              type="dashboard"
              :percentage="ticket.sellerScore"
              :color="getScoreColor(ticket.sellerScore)"
              :width="120"
            >
              <template #default="{ percentage }">
                <span class="score-value">{{ percentage }}</span>
              </template>
            </el-progress>
            <div class="score-details">
              <el-descriptions :column="1" size="small">
                <el-descriptions-item label="近30天维权数">{{ ticket.sellerStats.disputes }}</el-descriptions-item>
                <el-descriptions-item label="胜诉率">{{ ticket.sellerStats.winRate }}%</el-descriptions-item>
                <el-descriptions-item label="平均处理时效">{{ ticket.sellerStats.avgTime }}小时</el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showUpload" title="上传图片证据" width="500px">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleUploadChange"
        :limit="3"
        list-type="picture-card"
      >
        <el-icon><Plus /></el-icon>
      </el-upload>
      <template #footer>
        <el-button @click="showUpload = false">取消</el-button>
        <el-button type="primary" @click="confirmUpload" :loading="uploading">确认上传</el-button>
      </template>
    </el-dialog>

    <el-image-viewer
      v-if="previewVisible"
      :url-list="previewUrls"
      :initial-index="previewIndex"
      @close="previewVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Upload, Picture, Paperclip } from '@element-plus/icons-vue'

const route = useRoute()

const chatContainer = ref(null)
const previewVisible = ref(false)
const previewUrls = ref([])
const previewIndex = ref(0)
const showUpload = ref(false)
const uploading = ref(false)
const uploadFiles = ref([])
const evidenceFiles = ref([])
const newMessage = ref('')

const ticket = ref({
  id: 1,
  ticketNo: 'WT202604290001',
  orderNo: 'ORD20260428001',
  title: '申请仅退款 - 商品质量问题',
  productName: 'XX品牌手机 128G',
  type: 'refund',
  status: 'evidence',
  amount: 3999,
  createTime: '2026-04-29 10:30:00',
  sellerName: '某某官方旗舰店',
  description: '收到商品后发现屏幕有划痕，电池续航严重不足，申请仅退款处理。',
  slaRemaining: '12小时30分',
  slaPercentage: 40,
  autoDecision: 'refund',
  decisionConfidence: 85,
  decisionRules: [
    '买家提供了有效的质量问题照片证据',
    '商品在7天无理由退换货期限内',
    '商家近30天同类问题投诉3起'
  ],
  sellerScore: 92.5,
  sellerStats: {
    disputes: 15,
    winRate: 85,
    avgTime: 12
  }
})

const messages = ref([
  {
    id: 1,
    type: 'buyer',
    fromType: 'buyer',
    time: '2026-04-29 10:35:00',
    content: '您好，我收到商品后发现屏幕有划痕，电池续航也有问题，请帮我处理退款。',
    evidence: '划痕照片_20260429.jpg'
  },
  {
    id: 2,
    type: 'system',
    fromType: 'system',
    time: '2026-04-29 10:36:00',
    content: '系统已自动识别图片证据，检测到屏幕划痕问题。'
  }
])

const similarCases = ref([
  {
    id: 101,
    title: '手机屏幕划痕退款案例',
    time: '2026-04-20',
    type: 'success',
    decision: '支持退款',
    similarity: 92
  },
  {
    id: 102,
    title: '电子产品质量问题维权',
    time: '2026-04-15',
    type: 'primary',
    decision: '支持退货退款',
    similarity: 85
  },
  {
    id: 103,
    title: '电池续航问题投诉处理',
    time: '2026-04-10',
    type: 'warning',
    decision: '部分退款',
    similarity: 78
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

const getSlaType = (remaining) => {
  if (remaining.startsWith('-')) return 'danger'
  const hours = parseInt(remaining)
  if (hours < 6) return 'danger'
  if (hours < 12) return 'warning'
  return 'success'
}

const getSlaProgressColor = (percentage) => {
  if (percentage > 100) return '#f56c6c'
  if (percentage > 80) return '#e6a23c'
  return '#67c23a'
}

const getFromText = (fromType) => {
  const map = { buyer: '买家', seller: '商家', system: '系统', arbitrator: '仲裁员' }
  return map[fromType] || fromType
}

const getDecisionText = (decision) => {
  const map = {
    refund: '判定: 支持买家退款申请',
    return: '判定: 支持退货退款',
    reject: '判定: 驳回申请',
    seller_responsible: '判定: 商家承担主要责任',
    buyer_responsible: '判定: 买家承担主要责任',
    partial_refund: '判定: 支持部分退款'
  }
  return map[decision] || decision
}

const getDecisionAlertType = (decision) => {
  const map = {
    refund: 'success',
    return: 'success',
    reject: 'error',
    seller_responsible: 'warning',
    buyer_responsible: 'info',
    partial_refund: 'warning'
  }
  return map[decision] || 'info'
}

const getScoreColor = (score) => {
  if (score >= 90) return '#67c23a'
  if (score >= 70) return '#409eff'
  return '#f56c6c'
}

const handlePreview = (file) => {
  previewUrls.value = [file.url]
  previewIndex.value = 0
  previewVisible.value = true
}

const handleEvidenceChange = (file) => {
  console.log('证据文件:', file)
}

const handleUploadChange = (file, files) => {
  uploadFiles.value = files
}

const uploadEvidence = () => {
  ElMessage.success('证据上传成功')
}

const sendMessage = () => {
  if (!newMessage.value.trim()) return
  
  messages.value.push({
    id: Date.now(),
    type: 'buyer',
    fromType: 'buyer',
    time: new Date().toLocaleString(),
    content: newMessage.value
  })
  
  newMessage.value = ''
  
  setTimeout(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  }, 100)
}

const confirmUpload = () => {
  uploading.value = true
  setTimeout(() => {
    uploading.value = false
    showUpload.value = false
    ElMessage.success('图片上传成功，系统正在分析...')
  }, 1500)
}

const acceptDecision = () => {
  ElMessage.success('已接受自动判定结果，工单进入执行阶段')
}

const escalate = () => {
  ElMessage.warning('已提交平台介入申请，仲裁员将尽快处理')
}

const viewCase = (id) => {
  console.log('查看案例:', id)
}

onMounted(() => {
  const ticketId = route.params.id
  console.log('工单ID:', ticketId)
})
</script>

<style scoped>
.ticket-detail {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ticket-title {
  font-size: 18px;
  font-weight: bold;
}

.ticket-no {
  color: #909399;
}

.ticket-info {
  margin-bottom: 20px;
}

.description-section, .evidence-section, .chat-section {
  margin-bottom: 20px;
}

.description-section h4, .evidence-section h4, .chat-section h4 {
  margin-bottom: 12px;
  color: #303133;
}

.upload-btn {
  margin-top: 10px;
}

.chat-container {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 15px;
}

.chat-message {
  margin-bottom: 15px;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border-left: 3px solid #409eff;
}

.chat-message.buyer {
  border-left-color: #409eff;
}

.chat-message.seller {
  border-left-color: #67c23a;
}

.chat-message.system {
  border-left-color: #909399;
  background: #f0f2f5;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.message-content {
  line-height: 1.6;
  color: #303133;
}

.message-evidence {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #dcdfe6;
}

.chat-input {
  border-top: 1px solid #ebeef5;
  padding-top: 15px;
}

.chat-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
}

.sla-panel, .decision-panel, .cases-panel, .score-panel {
  padding: 5px 0;
}

.sla-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.sla-time {
  font-weight: bold;
}

.sla-warnings {
  margin-top: 15px;
}

.auto-decision-card, .similar-cases-card, .seller-score-card {
  margin-top: 20px;
}

.decision-actions {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.decision-actions .el-button {
  flex: 1;
}

.decision-details ul {
  margin: 10px 0 0 20px;
}

.decision-pending {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.case-card {
  cursor: pointer;
  padding: 10px;
}

.case-title {
  font-weight: bold;
  margin-bottom: 8px;
}

.case-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.score-value {
  font-size: 24px;
  font-weight: bold;
}

.score-details {
  width: 100%;
}
</style>
