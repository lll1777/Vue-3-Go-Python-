<template>
  <div class="create-ticket">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>创建维权工单</span>
          <el-text type="info">请详细描述您的问题并提供相关证据</el-text>
        </div>
      </template>

      <el-form
        ref="ticketFormRef"
        :model="ticketForm"
        :rules="ticketRules"
        label-width="120px"
        class="ticket-form"
      >
        <el-divider content-position="left">订单信息</el-divider>
        
        <el-form-item label="订单号" prop="orderNo">
          <el-input
            v-model="ticketForm.orderNo"
            placeholder="请输入订单号"
            size="large"
          />
          <el-button type="primary" size="large" @click="searchOrder">
            查询订单
          </el-button>
        </el-form-item>

        <div v-if="orderInfo" class="order-preview">
          <el-card shadow="never">
            <el-descriptions :column="3" border size="small">
              <el-descriptions-item label="商品名称">{{ orderInfo.productName }}</el-descriptions-item>
              <el-descriptions-item label="订单金额">{{ orderInfo.amount }} 元</el-descriptions-item>
              <el-descriptions-item label="商家">{{ orderInfo.sellerName }}</el-descriptions-item>
              <el-descriptions-item label="下单时间">{{ orderInfo.orderTime }}</el-descriptions-item>
              <el-descriptions-item label="收货状态">
                <el-tag :type="orderInfo.received ? 'success' : 'warning'">
                  {{ orderInfo.received ? '已收货' : '待收货' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="订单状态">
                <el-tag type="primary">{{ orderInfo.status }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </div>

        <el-divider content-position="left">维权类型</el-divider>

        <el-form-item label="维权类型" prop="type">
          <el-radio-group v-model="ticketForm.type" size="large">
            <el-radio-button label="refund">
              <el-icon><Refund /></el-icon> 仅退款
            </el-radio-button>
            <el-radio-button label="return">
              <el-icon><Goods /></el-icon> 退货退款
            </el-radio-button>
            <el-radio-button label="complaint">
              <el-icon><Warning /></el-icon> 投诉
            </el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="问题分类" prop="category">
          <el-cascader
            v-model="ticketForm.category"
            :options="categoryOptions"
            :props="{ multiple: false, label: 'label', value: 'value', children: 'children' }"
            placeholder="请选择问题分类"
            size="large"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="申请金额" prop="amount">
          <el-input-number
            v-model="ticketForm.amount"
            :min="0"
            :max="orderInfo?.amount || 999999"
            :precision="2"
            size="large"
            style="width: 300px"
          />
          <el-text type="info" class="hint-text">订单金额: {{ orderInfo?.amount || 0 }} 元</el-text>
        </el-form-item>

        <el-divider content-position="left">问题描述</el-divider>

        <el-form-item label="问题标题" prop="title">
          <el-input
            v-model="ticketForm.title"
            placeholder="请简要描述您的问题"
            size="large"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="详细描述" prop="description">
          <el-input
            v-model="ticketForm.description"
            type="textarea"
            :rows="6"
            placeholder="请详细描述您遇到的问题，包括：
1. 问题发生的时间和场景
2. 您的诉求是什么
3. 希望如何解决
"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>

        <el-divider content-position="left">举证材料</el-divider>

        <el-form-item label="图片证据">
          <el-upload
            v-model:file-list="evidenceImages"
            list-type="picture-card"
            :auto-upload="false"
            :limit="9"
            multiple
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="el-upload__tip">
                支持jpg/png/gif格式，最多上传9张图片
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="图片分析">
          <el-button type="warning" :icon="MagicStick" @click="analyzeImages" :loading="analyzing">
            智能分析图片证据
          </el-button>
          <el-text type="info" class="hint-text">
            系统将自动识别图片中的虚假宣传、质量问题等
          </el-text>
        </el-form-item>

        <div v-if="analysisResult" class="analysis-result">
          <el-alert :title="analysisResult.title" :type="analysisResult.type" show-icon>
            <template #default>
              <div class="analysis-details">
                <p><strong>识别结果:</strong> {{ analysisResult.result }}</p>
                <p><strong>置信度:</strong> {{ analysisResult.confidence }}%</p>
                <p v-if="analysisResult.suggestion"><strong>建议:</strong> {{ analysisResult.suggestion }}</p>
              </div>
            </template>
          </el-alert>
        </div>

        <el-form-item label="视频/其他">
          <el-upload
            v-model:file-list="otherFiles"
            :auto-upload="false"
            :limit="3"
            multiple
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon> 上传视频/文档
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持mp4/avi/pdf/doc等格式，最多上传3个文件
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-divider />

        <el-form-item>
          <el-button type="primary" size="large" @click="submitTicket" :loading="submitting">
            <el-icon><Check /></el-icon> 提交维权申请
          </el-button>
          <el-button size="large" @click="resetForm">
            <el-icon><Refresh /></el-icon> 重置
          </el-button>
          <el-button size="large" @click="saveDraft">
            <el-icon><Document /></el-icon> 保存草稿
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Refund, Goods, Warning, Plus, MagicStick,
  Upload, Check, Refresh, Document
} from '@element-plus/icons-vue'

const router = useRouter()

const ticketFormRef = ref(null)
const submitting = ref(false)
const analyzing = ref(false)
const evidenceImages = ref([])
const otherFiles = ref([])
const analysisResult = ref(null)

const orderInfo = ref(null)

const ticketForm = reactive({
  orderNo: '',
  type: 'refund',
  category: [],
  amount: 0,
  title: '',
  description: ''
})

const ticketRules = {
  orderNo: [{ required: true, message: '请输入订单号', trigger: 'blur' }],
  type: [{ required: true, message: '请选择维权类型', trigger: 'change' }],
  category: [{ required: true, message: '请选择问题分类', trigger: 'change' }],
  amount: [
    { required: true, message: '请输入申请金额', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '金额必须大于0', trigger: 'blur' }
  ],
  title: [
    { required: true, message: '请输入问题标题', trigger: 'blur' },
    { min: 5, max: 100, message: '标题长度在5-100个字符之间', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入详细描述', trigger: 'blur' },
    { min: 20, max: 2000, message: '描述长度在20-2000个字符之间', trigger: 'blur' }
  ]
}

const categoryOptions = [
  {
    value: 'quality',
    label: '质量问题',
    children: [
      { value: 'defect', label: '商品有缺陷' },
      { value: 'damage', label: '商品损坏' },
      { value: 'not_work', label: '无法正常使用' },
      { value: 'counterfeit', label: '假冒伪劣' }
    ]
  },
  {
    value: 'logistics',
    label: '物流问题',
    children: [
      { value: 'late', label: '延迟发货' },
      { value: 'lost', label: '商品丢失' },
      { value: 'wrong', label: '发错商品' },
      { value: 'missing', label: '少发漏发' }
    ]
  },
  {
    value: 'service',
    label: '服务问题',
    children: [
      { value: 'rude', label: '客服态度差' },
      { value: 'refuse', label: '拒绝售后' },
      { value: 'slow', label: '响应缓慢' },
      { value: 'mislead', label: '误导消费' }
    ]
  },
  {
    value: 'advertising',
    label: '宣传问题',
    children: [
      { value: 'false', label: '虚假宣传' },
      { value: 'exaggerate', label: '夸大宣传' },
      { value: 'price', label: '价格欺诈' }
    ]
  }
]

const searchOrder = () => {
  if (!ticketForm.orderNo) {
    ElMessage.warning('请输入订单号')
    return
  }
  
  orderInfo.value = {
    productName: 'XX品牌智能手机 128G 星空灰',
    amount: 3999.00,
    sellerName: '某某官方旗舰店',
    orderTime: '2026-04-25 14:30:00',
    received: true,
    status: '已完成'
  }
  
  ticketForm.amount = orderInfo.value.amount
  ElMessage.success('订单查询成功')
}

const analyzeImages = () => {
  if (evidenceImages.value.length === 0) {
    ElMessage.warning('请先上传图片证据')
    return
  }
  
  analyzing.value = true
  
  setTimeout(() => {
    analyzing.value = false
    analysisResult.value = {
      title: '图片智能分析结果',
      type: 'warning',
      result: '检测到图片中存在商品质量问题：屏幕划痕明显，疑似二手商品',
      confidence: 92,
      suggestion: '建议您补充更多证据，系统判定您的退款申请有较高成功率'
    }
    ElMessage.success('图片分析完成')
  }, 2000)
}

const submitTicket = async () => {
  if (!ticketFormRef.value) return
  
  await ticketFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      
      setTimeout(() => {
        submitting.value = false
        ElMessage.success('维权工单创建成功！')
        router.push('/tickets')
      }, 1500)
    }
  })
}

const resetForm = () => {
  if (ticketFormRef.value) {
    ticketFormRef.value.resetFields()
  }
  orderInfo.value = null
  evidenceImages.value = []
  otherFiles.value = []
  analysisResult.value = null
}

const saveDraft = () => {
  ElMessage.success('草稿已保存')
}
</script>

<style scoped>
.create-ticket {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ticket-form {
  max-width: 900px;
  margin: 0 auto;
}

.order-preview {
  margin-bottom: 20px;
}

.hint-text {
  margin-left: 15px;
}

.analysis-result {
  margin-top: 15px;
}

.analysis-details {
  margin-top: 10px;
}

.analysis-details p {
  margin-bottom: 5px;
}
</style>
