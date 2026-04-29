<template>
  <div class="cases-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>案例库</span>
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
            新增案例
          </el-button>
        </div>
      </template>

      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="请输入关键词搜索"
            prefix-icon="Search"
            clearable
            style="width: 250px"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="searchForm.category" placeholder="全部分类" clearable>
            <el-option label="质量问题" value="quality" />
            <el-option label="虚假宣传" value="advertising" />
            <el-option label="物流问题" value="logistics" />
            <el-option label="服务问题" value="service" />
            <el-option label="退款退货" value="refund" />
          </el-select>
        </el-form-item>
        <el-form-item label="判定结果">
          <el-select v-model="searchForm.decision" placeholder="全部判定" clearable>
            <el-option label="支持退款" value="refund" />
            <el-option label="支持退货退款" value="return" />
            <el-option label="部分退款" value="partial_refund" />
            <el-option label="商家责任" value="seller_responsible" />
            <el-option label="买家责任" value="buyer_responsible" />
            <el-option label="驳回申请" value="reject" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="casesList" v-loading="loading" style="width: 100%">
        <el-table-column prop="caseNo" label="案例编号" width="150" />
        <el-table-column prop="title" label="案例标题" min-width="250">
          <template #default="scope">
            <el-link type="primary" @click="viewCase(scope.row)">
              {{ scope.row.title }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="120">
          <template #default="scope">
            <el-tag :type="getCategoryTag(scope.row.category)" size="small">
              {{ getCategoryText(scope.row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="decision" label="判定结果" width="130">
          <template #default="scope">
            <el-tag :type="getDecisionTag(scope.row.decision)" size="small">
              {{ getDecisionText(scope.row.decision) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" min-width="180">
          <template #default="scope">
            <div class="tags-container">
              <el-tag
                v-for="tag in scope.row.tags.slice(0, 3)"
                :key="tag"
                size="small"
                style="margin-right: 5px; margin-bottom: 5px"
              >
                {{ tag }}
              </el-tag>
              <el-tag v-if="scope.row.tags.length > 3" size="small" type="info">
                +{{ scope.row.tags.length - 3 }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="viewCount" label="浏览量" width="80" align="center" />
        <el-table-column prop="referenceCount" label="引用次数" width="80" align="center" />
        <el-table-column prop="createdAt" label="创建时间" width="160" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="viewCase(scope.row)">
              详情
            </el-button>
            <el-button type="primary" link @click="analyzeCase(scope.row)">
              分析
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

    <el-dialog v-model="showViewDialog" title="案例详情" width="800px">
      <el-descriptions :column="2" border v-if="currentCase">
        <el-descriptions-item label="案例编号">{{ currentCase.caseNo }}</el-descriptions-item>
        <el-descriptions-item label="案例标题">{{ currentCase.title }}</el-descriptions-item>
        <el-descriptions-item label="分类">
          <el-tag :type="getCategoryTag(currentCase.category)">
            {{ getCategoryText(currentCase.category) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="判定结果">
          <el-tag :type="getDecisionTag(currentCase.decision)">
            {{ getDecisionText(currentCase.decision) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="浏览量">{{ currentCase.viewCount }}</el-descriptions-item>
        <el-descriptions-item label="引用次数">{{ currentCase.referenceCount }}</el-descriptions-item>
        <el-descriptions-item label="标签" :span="2">
          <el-tag v-for="tag in currentCase.tags" :key="tag" size="small" style="margin-right: 5px">
            {{ tag }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">案件事实</el-divider>
      <el-card shadow="never">
        <el-text>{{ currentCase?.facts }}</el-text>
      </el-card>

      <el-divider content-position="left">证据材料</el-divider>
      <el-card shadow="never">
        <el-text>{{ currentCase?.evidence }}</el-text>
      </el-card>

      <el-divider content-position="left">判定理由</el-divider>
      <el-card shadow="never">
        <el-text>{{ currentCase?.decisionReason }}</el-text>
      </el-card>

      <el-divider content-position="left">适用规则</el-divider>
      <el-card shadow="never">
        <div v-if="currentCase?.rulesApplied?.length > 0">
          <el-tag v-for="rule in currentCase.rulesApplied" :key="rule" type="primary" style="margin-right: 10px">
            {{ rule }}
          </el-tag>
        </div>
        <el-text type="info" v-else>无适用规则记录</el-text>
      </el-card>
    </el-dialog>

    <el-dialog v-model="showAnalysisDialog" title="案例相似性分析" width="700px">
      <div v-if="analysisResult">
        <el-alert
          :title="analysisResult.recommendation"
          :type="getRecommendationType(analysisResult.applicabilityScore)"
          show-icon
        >
          <template #default>
            <p><strong>适用度评分:</strong> {{ analysisResult.applicabilityScore }}%</p>
            <p><strong>匹配原因:</strong></p>
            <ul>
              <li v-for="reason in analysisResult.matchReasons" :key="reason">{{ reason }}</li>
            </ul>
          </template>
        </el-alert>

        <el-divider content-position="left">匹配详情</el-divider>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="类别匹配">{{ analysisResult.categoryMatch ? '是' : '否' }}</el-descriptions-item>
          <el-descriptions-item label="标签相似度">{{ analysisResult.tagSimilarity }}%</el-descriptions-item>
          <el-descriptions-item label="描述相似度">{{ analysisResult.descriptionSimilarity }}%</el-descriptions-item>
          <el-descriptions-item label="决策权重">{{ analysisResult.decisionWeight }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="showAnalysisDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showCreateDialog" title="新增案例" width="700px">
      <el-form :model="newCaseForm" :rules="newCaseRules" ref="newCaseFormRef" label-width="100px">
        <el-form-item label="案例标题" prop="title">
          <el-input v-model="newCaseForm.title" placeholder="请输入案例标题" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-select v-model="newCaseForm.category" placeholder="请选择分类" style="width: 100%">
                <el-option label="质量问题" value="quality" />
                <el-option label="虚假宣传" value="advertising" />
                <el-option label="物流问题" value="logistics" />
                <el-option label="服务问题" value="service" />
                <el-option label="退款退货" value="refund" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="判定结果" prop="decision">
              <el-select v-model="newCaseForm.decision" placeholder="请选择判定结果" style="width: 100%">
                <el-option label="支持退款" value="refund" />
                <el-option label="支持退货退款" value="return" />
                <el-option label="部分退款" value="partial_refund" />
                <el-option label="商家责任" value="seller_responsible" />
                <el-option label="买家责任" value="buyer_responsible" />
                <el-option label="驳回申请" value="reject" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="案件事实" prop="facts">
          <el-input v-model="newCaseForm.facts" type="textarea" :rows="3" placeholder="请输入案件事实" />
        </el-form-item>
        <el-form-item label="证据材料" prop="evidence">
          <el-input v-model="newCaseForm.evidence" type="textarea" :rows="2" placeholder="请输入证据材料" />
        </el-form-item>
        <el-form-item label="判定理由" prop="decisionReason">
          <el-input v-model="newCaseForm.decisionReason" type="textarea" :rows="3" placeholder="请输入判定理由" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="newCaseForm.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请选择或输入标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in suggestedTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createCase" :loading="creating">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'

const loading = ref(false)
const creating = ref(false)
const showViewDialog = ref(false)
const showAnalysisDialog = ref(false)
const showCreateDialog = ref(false)
const currentCase = ref(null)
const analysisResult = ref(null)

const searchForm = reactive({
  keyword: '',
  category: '',
  decision: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 8
})

const newCaseForm = reactive({
  title: '',
  category: '',
  decision: '',
  facts: '',
  evidence: '',
  decisionReason: '',
  tags: []
})

const newCaseRules = {
  title: [{ required: true, message: '请输入案例标题', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  decision: [{ required: true, message: '请选择判定结果', trigger: 'change' }],
  facts: [{ required: true, message: '请输入案件事实', trigger: 'blur' }],
  decisionReason: [{ required: true, message: '请输入判定理由', trigger: 'blur' }]
}

const suggestedTags = [
  '质量问题', '虚假宣传', '物流', '客服', '退货', '退款',
  '划痕', '破损', '二手', '假货', '价格欺诈', '延迟发货'
]

const casesList = ref([
  {
    id: 1,
    caseNo: 'CASE2026001',
    title: '手机屏幕划痕退款案例',
    category: 'quality',
    subCategory: 'defect',
    decision: 'refund',
    facts: '买家提供了3张清晰的照片证据，显示屏幕存在深度划痕。商品在签收后第3天申请退款，在7天无理由退货期限内。',
    evidence: '照片证据、快递签收记录、聊天记录',
    decisionReason: '证据充分，支持退款申请。买家提供了清晰的划痕照片，且在7天退货期限内。',
    rulesApplied: ['RULE_001', 'RULE_002'],
    tags: ['手机', '质量问题', '划痕', '退款'],
    viewCount: 156,
    referenceCount: 23,
    createdAt: '2026-04-15 10:30:00'
  },
  {
    id: 2,
    caseNo: 'CASE2026002',
    title: '虚假宣传案例-续航能力',
    category: 'advertising',
    subCategory: 'false',
    decision: 'seller_responsible',
    facts: '商品宣传页声称续航48小时，但买家实际测试仅12小时。买家提供了商品宣传页截图和实际测试数据。',
    evidence: '宣传截图、测试视频、聊天记录',
    decisionReason: '检测到虚假宣传，判定商家承担全部责任。商家宣传的续航能力与实际情况严重不符。',
    rulesApplied: ['RULE_003'],
    tags: ['虚假宣传', '续航', '商家责任', '三倍赔偿'],
    viewCount: 289,
    referenceCount: 45,
    createdAt: '2026-04-12 14:20:00'
  },
  {
    id: 3,
    caseNo: 'CASE2026003',
    title: '电子产品退货案例',
    category: 'refund',
    subCategory: 'return',
    decision: 'return',
    facts: '买家在签收后第5天申请无理由退货，商品保存完好，包装齐全。',
    evidence: '快递签收记录、商品照片',
    decisionReason: '符合7天无理由退货条件，支持退货退款申请。',
    rulesApplied: ['RULE_001'],
    tags: ['7天无理由', '退货', '电子产品'],
    viewCount: 98,
    referenceCount: 12,
    createdAt: '2026-04-10 09:15:00'
  },
  {
    id: 4,
    caseNo: 'CASE2026004',
    title: '延迟发货投诉案例',
    category: 'logistics',
    subCategory: 'late',
    decision: 'refund',
    facts: '卖家承诺48小时发货，但买家支付后7天仍未发货。订单显示支付成功，但物流信息始终未更新。',
    evidence: '订单截图、聊天记录、物流查询记录',
    decisionReason: '卖家未能按时发货，违反了发货承诺，支持退款申请。',
    rulesApplied: ['RULE_007'],
    tags: ['延迟发货', '物流', '退款'],
    viewCount: 134,
    referenceCount: 18,
    createdAt: '2026-04-08 16:45:00'
  },
  {
    id: 5,
    caseNo: 'CASE2026005',
    title: '二手商品冒充新品案例',
    category: 'quality',
    subCategory: 'counterfeit',
    decision: 'seller_responsible',
    facts: '卖家宣传全新商品，但收到的商品有明显使用痕迹，电池循环次数超过50次。',
    evidence: '商品照片、检测报告、系统信息截图',
    decisionReason: '商品与描述不符，涉嫌欺诈，判定商家承担全部责任。',
    rulesApplied: ['RULE_003', 'RULE_009'],
    tags: ['二手商品', '欺诈', '商家责任', '三倍赔偿'],
    viewCount: 412,
    referenceCount: 67,
    createdAt: '2026-04-05 11:30:00'
  }
])

const getCategoryText = (category) => {
  const map = {
    quality: '质量问题',
    advertising: '虚假宣传',
    logistics: '物流问题',
    service: '服务问题',
    refund: '退款退货'
  }
  return map[category] || category
}

const getCategoryTag = (category) => {
  const map = {
    quality: 'success',
    advertising: 'warning',
    logistics: 'info',
    service: 'danger',
    refund: 'primary'
  }
  return map[category] || 'info'
}

const getDecisionText = (decision) => {
  const map = {
    refund: '支持退款',
    return: '支持退货退款',
    partial_refund: '部分退款',
    seller_responsible: '商家责任',
    buyer_responsible: '买家责任',
    reject: '驳回申请'
  }
  return map[decision] || decision
}

const getDecisionTag = (decision) => {
  const map = {
    refund: 'success',
    return: 'success',
    partial_refund: 'primary',
    seller_responsible: 'danger',
    buyer_responsible: 'warning',
    reject: 'info'
  }
  return map[decision] || 'info'
}

const getRecommendationType = (score) => {
  if (score >= 80) return 'success'
  if (score >= 60) return 'warning'
  return 'info'
}

const handleSearch = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 500)
}

const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    category: '',
    decision: ''
  })
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
}

const handleCurrentChange = (val) => {
  pagination.page = val
}

const viewCase = (row) => {
  currentCase.value = row
  showViewDialog.value = true
}

const analyzeCase = (row) => {
  currentCase.value = row
  analysisResult.value = {
    applicabilityScore: 78,
    recommendation: '建议参考此案例',
    matchReasons: [
      '类别匹配：质量问题',
      '标签相似度较高',
      '描述相似度75%',
      '适用相同的判定规则'
    ],
    categoryMatch: true,
    tagSimilarity: 65,
    descriptionSimilarity: 75,
    decisionWeight: 1.0
  }
  showAnalysisDialog.value = true
}

const createCase = () => {
  creating.value = true
  setTimeout(() => {
    creating.value = false
    showCreateDialog.value = false
    ElMessage.success('案例创建成功')
    Object.assign(newCaseForm, {
      title: '',
      category: '',
      decision: '',
      facts: '',
      evidence: '',
      decisionReason: '',
      tags: []
    })
  }, 1000)
}
</script>

<style scoped>
.cases-page {
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

.tags-container {
  display: flex;
  flex-wrap: wrap;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
