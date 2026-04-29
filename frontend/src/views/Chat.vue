<template>
  <div class="chat-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>协商聊天</span>
          <div class="header-info">
            <el-tag size="small">工单: {{ currentTicket?.ticketNo || '未选择' }}</el-tag>
            <el-tag :type="getStatusTag(currentTicket?.status)" size="small" v-if="currentTicket">
              {{ getStatusText(currentTicket.status) }}
            </el-tag>
          </div>
        </div>
      </template>

      <div class="chat-layout">
        <div class="ticket-list">
          <div class="list-header">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索工单..."
              :prefix-icon="Search"
              clearable
            />
          </div>
          <div class="ticket-items">
            <div
              v-for="ticket in ticketList"
              :key="ticket.id"
              :class="['ticket-item', { active: currentTicket?.id === ticket.id }]"
              @click="selectTicket(ticket)"
            >
              <div class="ticket-info">
                <div class="ticket-title">{{ ticket.title }}</div>
                <div class="ticket-no">{{ ticket.ticketNo }}</div>
              </div>
              <div class="ticket-meta">
                <el-tag :type="getStatusTag(ticket.status)" size="small">
                  {{ getStatusText(ticket.status) }}
                </el-tag>
                <el-text type="info" size="small">{{ ticket.lastMessage }}</el-text>
              </div>
            </div>
          </div>
        </div>

        <div class="chat-area">
          <div v-if="!currentTicket" class="empty-state">
            <el-empty description="请从左侧选择一个工单开始聊天" />
          </div>
          <div v-else class="chat-content">
            <div class="chat-messages" ref="messagesContainer">
              <div
                v-for="msg in messages"
                :key="msg.id"
                :class="['message-item', msg.type]"
              >
                <div class="message-avatar">
                  <el-avatar :size="40">
                    <el-icon :size="24"><User /></el-icon>
                  </el-avatar>
                </div>
                <div class="message-bubble">
                  <div class="message-header">
                    <span class="sender-name">{{ msg.senderName }}</span>
                    <el-tag :type="getSenderTag(msg.fromType)" size="small">
                      {{ getSenderText(msg.fromType) }}
                    </el-tag>
                    <span class="message-time">{{ msg.time }}</span>
                  </div>
                  <div class="message-text">{{ msg.content }}</div>
                  <div v-if="msg.evidence" class="message-evidence">
                    <el-link type="primary" :icon="Paperclip">
                      {{ msg.evidence }}
                    </el-link>
                  </div>
                </div>
              </div>

              <div v-if="loadingMessages" class="loading-messages">
                <el-icon class="is-loading" :size="24"><Loading /></el-icon>
                <el-text type="info">加载中...</el-text>
              </div>
            </div>

            <div class="chat-input-area">
              <div class="input-tools">
                <el-button type="primary" link :icon="Picture" @click="showUpload = true">
                  上传图片
                </el-button>
                <el-button type="primary" link :icon="Document">
                  上传文件
                </el-button>
              </div>
              <el-input
                v-model="newMessage"
                type="textarea"
                :rows="3"
                placeholder="输入消息内容..."
                @keyup.enter.ctrl="sendMessage"
              />
              <div class="input-actions">
                <el-text type="info" size="small">Ctrl + Enter 发送</el-text>
                <el-button type="primary" @click="sendMessage" :loading="sending">
                  <el-icon><Promotion /></el-icon> 发送
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <el-dialog v-model="showUpload" title="上传证据图片" width="500px">
      <el-upload
        :auto-upload="false"
        :on-change="handleFileChange"
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search, User, Paperclip, Picture, Document,
  Loading, Promotion, Plus
} from '@element-plus/icons-vue'

const route = useRoute()

const searchKeyword = ref('')
const currentTicket = ref(null)
const messagesContainer = ref(null)
const newMessage = ref('')
const showUpload = ref(false)
const loadingMessages = ref(false)
const sending = ref(false)
const uploading = ref(false)
const uploadFiles = ref([])

const ticketList = ref([
  {
    id: 1,
    ticketNo: 'WT202604290001',
    title: '申请仅退款 - 商品质量问题',
    status: 'negotiation',
    lastMessage: '请提供更多证据...'
  },
  {
    id: 2,
    ticketNo: 'WT202604290002',
    title: '退货退款申请',
    status: 'evidence',
    lastMessage: '等待商家回应...'
  },
  {
    id: 3,
    ticketNo: 'WT202604290003',
    title: '虚假宣传投诉',
    status: 'arbitration',
    lastMessage: '仲裁员已介入...'
  }
])

const messages = ref([
  {
    id: 1,
    type: 'buyer',
    fromType: 'buyer',
    senderName: '张三',
    time: '2026-04-29 10:35:00',
    content: '您好，我收到商品后发现屏幕有划痕，电池续航也有问题，请帮我处理退款。',
    evidence: '划痕照片_20260429.jpg'
  },
  {
    id: 2,
    type: 'system',
    fromType: 'system',
    senderName: '系统',
    time: '2026-04-29 10:36:00',
    content: '系统已自动识别图片证据，检测到屏幕划痕问题。'
  },
  {
    id: 3,
    type: 'seller',
    fromType: 'seller',
    senderName: '某某官方旗舰店',
    time: '2026-04-29 10:40:00',
    content: '您好，非常抱歉给您带来了不好的体验。请问您能提供更清晰的照片吗？我们需要确认问题的具体情况。'
  },
  {
    id: 4,
    type: 'buyer',
    fromType: 'buyer',
    senderName: '张三',
    time: '2026-04-29 10:45:00',
    content: '好的，我再拍几张清晰的照片上传。另外，电池续航真的很差，充满电只能用2小时左右，和宣传的12小时差太多了。'
  }
])

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

const getSenderText = (fromType) => {
  const map = {
    buyer: '买家',
    seller: '商家',
    system: '系统',
    arbitrator: '仲裁员'
  }
  return map[fromType] || fromType
}

const getSenderTag = (fromType) => {
  const map = {
    buyer: 'primary',
    seller: 'success',
    system: 'info',
    arbitrator: 'danger'
  }
  return map[fromType] || 'info'
}

const selectTicket = (ticket) => {
  currentTicket.value = ticket
  loadingMessages.value = true

  setTimeout(() => {
    loadingMessages.value = false
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  }, 500)
}

const handleFileChange = (file, files) => {
  uploadFiles.value = files
}

const sendMessage = () => {
  if (!newMessage.value.trim() || !currentTicket.value) return

  sending.value = true

  setTimeout(() => {
    messages.value.push({
      id: Date.now(),
      type: 'buyer',
      fromType: 'buyer',
      senderName: '我',
      time: new Date().toLocaleString(),
      content: newMessage.value
    })

    newMessage.value = ''
    sending.value = false

    setTimeout(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }, 100)

    ElMessage.success('消息发送成功')
  }, 800)
}

const confirmUpload = () => {
  uploading.value = true

  setTimeout(() => {
    uploading.value = false
    showUpload.value = false
    ElMessage.success('图片上传成功')
  }, 1500)
}

onMounted(() => {
  const ticketId = route.query.ticketId
  if (ticketId) {
    const ticket = ticketList.value.find(t => t.id === parseInt(ticketId))
    if (ticket) {
      selectTicket(ticket)
    }
  }
})
</script>

<style scoped>
.chat-page {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-info {
  display: flex;
  gap: 10px;
}

.chat-layout {
  display: flex;
  height: calc(100vh - 200px);
  gap: 20px;
}

.ticket-list {
  width: 300px;
  border-right: 1px solid #ebeef5;
  padding-right: 20px;
  display: flex;
  flex-direction: column;
}

.list-header {
  margin-bottom: 15px;
}

.ticket-items {
  flex: 1;
  overflow-y: auto;
}

.ticket-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 10px;
  border: 1px solid #ebeef5;
  transition: all 0.2s;
}

.ticket-item:hover {
  background: #f5f7fa;
}

.ticket-item.active {
  background: #ecf5ff;
  border-color: #409eff;
}

.ticket-info {
  margin-bottom: 8px;
}

.ticket-title {
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ticket-no {
  font-size: 12px;
  color: #909399;
}

.ticket-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.chat-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.message-item {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-item.buyer {
  flex-direction: row-reverse;
}

.message-item.buyer .message-bubble {
  background: #409eff;
  color: white;
}

.message-item.system .message-bubble {
  background: #f0f2f5;
  color: #606266;
  font-style: italic;
}

.message-avatar {
  flex-shrink: 0;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.sender-name {
  font-weight: bold;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

.message-text {
  line-height: 1.6;
}

.message-evidence {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.loading-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px;
}

.chat-input-area {
  background: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}

.input-tools {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}
</style>
