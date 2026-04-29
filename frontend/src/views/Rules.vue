<template>
  <div class="rules-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>规则引擎管理</span>
          <el-button type="primary" :icon="Plus" @click="showCreateDialog = true">
            新建规则
          </el-button>
        </div>
      </template>

      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="规则分类">
          <el-select v-model="searchForm.category" placeholder="全部分类" clearable>
            <el-option label="退款退货" value="refund" />
            <el-option label="质量问题" value="quality" />
            <el-option label="虚假宣传" value="advertising" />
            <el-option label="物流问题" value="logistics" />
            <el-option label="服务问题" value="service" />
            <el-option label="商家评分" value="seller_score" />
            <el-option label="买家信誉" value="buyer_credit" />
            <el-option label="SLA时效" value="sla" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.isActive" placeholder="全部状态" clearable>
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="rulesList" v-loading="loading" style="width: 100%">
        <el-table-column prop="code" label="规则代码" width="120" />
        <el-table-column prop="name" label="规则名称" min-width="180" />
        <el-table-column prop="category" label="分类" width="120">
          <template #default="scope">
            <el-tag :type="getCategoryTag(scope.row.category)" size="small">
              {{ getCategoryText(scope.row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.priority >= 80 ? 'danger' : scope.row.priority >= 50 ? 'warning' : 'info'" size="small">
              {{ scope.row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="weight" label="权重" width="80" align="center" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="isActive" label="状态" width="80" align="center">
          <template #default="scope">
            <el-switch
              v-model="scope.row.isActive"
              active-color="#13ce66"
              inactive-color="#ff4949"
              @change="toggleRuleStatus(scope.row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="70" align="center" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button type="primary" link @click="viewRule(scope.row)">
              查看
            </el-button>
            <el-button type="primary" link @click="editRule(scope.row)">
              编辑
            </el-button>
            <el-button type="primary" link @click="testRule(scope.row)">
              测试
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

    <el-dialog v-model="showCreateDialog" :title="isEdit ? '编辑规则' : '新建规则'" width="700px">
      <el-form :model="ruleForm" :rules="ruleRules" ref="ruleFormRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="规则代码" prop="code">
              <el-input v-model="ruleForm.code" placeholder="请输入规则代码" :disabled="isEdit" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="规则名称" prop="name">
              <el-input v-model="ruleForm.name" placeholder="请输入规则名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-select v-model="ruleForm.category" placeholder="请选择分类" style="width: 100%">
                <el-option label="退款退货" value="refund" />
                <el-option label="质量问题" value="quality" />
                <el-option label="虚假宣传" value="advertising" />
                <el-option label="物流问题" value="logistics" />
                <el-option label="服务问题" value="service" />
                <el-option label="商家评分" value="seller_score" />
                <el-option label="买家信誉" value="buyer_credit" />
                <el-option label="SLA时效" value="sla" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="优先级" prop="priority">
              <el-input-number v-model="ruleForm.priority" :min="0" :max="100" :step="10" />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="权重" prop="weight">
              <el-input-number v-model="ruleForm.weight" :min="0" :max="200" :step="5" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述" prop="description">
          <el-input v-model="ruleForm.description" type="textarea" :rows="2" placeholder="请输入规则描述" />
        </el-form-item>

        <el-form-item label="触发条件" prop="conditions">
          <el-input
            v-model="ruleForm.conditions"
            type="textarea"
            :rows="4"
            placeholder="请输入触发条件（JSON格式）"
          />
          <el-text type="info" size="small">
            例如: {"evidence_count": {"$gte": 1}, "category": "quality"}
          </el-text>
        </el-form-item>

        <el-form-item label="执行动作" prop="actions">
          <el-input
            v-model="ruleForm.actions"
            type="textarea"
            :rows="4"
            placeholder="请输入执行动作（JSON格式）"
          />
          <el-text type="info" size="small">
            例如: {"decision": "refund", "reason": "质量问题证据充分", "weight_bonus": 20}
          </el-text>
        </el-form-item>

        <el-form-item label="状态">
          <el-switch v-model="ruleForm.isActive" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRule" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showViewDialog" title="规则详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="规则代码">{{ currentRule?.code }}</el-descriptions-item>
        <el-descriptions-item label="规则名称">{{ currentRule?.name }}</el-descriptions-item>
        <el-descriptions-item label="分类">
          <el-tag :type="getCategoryTag(currentRule?.category)">{{ getCategoryText(currentRule?.category) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="优先级">{{ currentRule?.priority }}</el-descriptions-item>
        <el-descriptions-item label="权重">{{ currentRule?.weight }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentRule?.isActive ? 'success' : 'danger'">
            {{ currentRule?.isActive ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentRule?.description }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">触发条件</el-divider>
      <el-input
        :model-value="currentRule?.conditions"
        type="textarea"
        :rows="3"
        readonly
      />

      <el-divider content-position="left">执行动作</el-divider>
      <el-input
        :model-value="currentRule?.actions"
        type="textarea"
        :rows="3"
        readonly
      />
    </el-dialog>

    <el-dialog v-model="showTestDialog" title="规则测试" width="700px">
      <el-form label-width="120px">
        <el-form-item label="测试数据">
          <el-input
            v-model="testData"
            type="textarea"
            :rows="8"
            placeholder="请输入测试数据（JSON格式）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showTestDialog = false">取消</el-button>
        <el-button type="primary" @click="runTest" :loading="testing">执行测试</el-button>
      </template>

      <el-divider v-if="testResult" content-position="left">测试结果</el-divider>
      <el-alert
        v-if="testResult"
        :title="testResult.passed ? '测试通过' : '测试不通过'"
        :type="testResult.passed ? 'success' : 'error'"
        show-icon
      >
        <template #default>
          <p><strong>规则名称:</strong> {{ testResult.ruleName }}</p>
          <p><strong>匹配结果:</strong> {{ testResult.passed ? '条件匹配' : '条件不匹配' }}</p>
          <p v-if="testResult.message"><strong>说明:</strong> {{ testResult.message }}</p>
        </template>
      </el-alert>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const showCreateDialog = ref(false)
const showViewDialog = ref(false)
const showTestDialog = ref(false)
const isEdit = ref(false)
const currentRule = ref(null)
const testData = ref('')
const testResult = ref(null)

const searchForm = reactive({
  category: '',
  isActive: null
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 10
})

const ruleForm = reactive({
  id: null,
  code: '',
  name: '',
  category: '',
  priority: 50,
  weight: 100,
  description: '',
  conditions: '',
  actions: '',
  isActive: true,
  version: 1
})

const ruleRules = {
  code: [{ required: true, message: '请输入规则代码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  conditions: [{ required: true, message: '请输入触发条件', trigger: 'blur' }],
  actions: [{ required: true, message: '请输入执行动作', trigger: 'blur' }]
}

const rulesList = ref([
  {
    id: 1,
    code: 'RULE_001',
    name: '7天无理由退货',
    category: 'refund',
    priority: 100,
    weight: 100,
    description: '商品在7天退货期限内，支持无理由退货',
    conditions: '{"days_since_receive": {"$lte": 7}, "type": "return"}',
    actions: '{"decision": "return", "reason": "7天无理由退货"}',
    isActive: true,
    version: 1
  },
  {
    id: 2,
    code: 'RULE_002',
    name: '质量问题退款',
    category: 'quality',
    priority: 90,
    weight: 95,
    description: '图片证据显示存在明确质量问题，支持退款',
    conditions: '{"image_analysis.has_issue": true, "evidence_count": {"$gte": 1}}',
    actions: '{"decision": "refund", "reason": "质量问题证据充分", "weight_bonus": 20}',
    isActive: true,
    version: 1
  },
  {
    id: 3,
    code: 'RULE_003',
    name: '虚假宣传判定',
    category: 'advertising',
    priority: 95,
    weight: 98,
    description: '检测到虚假宣传内容，判定商家责任',
    conditions: '{"image_analysis.has_false_claim": true, "category": "advertising"}',
    actions: '{"decision": "seller_responsible", "reason": "虚假宣传", "seller_score_penalty": 5}',
    isActive: true,
    version: 1
  },
  {
    id: 4,
    code: 'RULE_004',
    name: '商家超时响应',
    category: 'sla',
    priority: 80,
    weight: 90,
    description: '商家在协商期内未响应，自动支持买家诉求',
    conditions: '{"stage": "negotiation", "sla_percentage": {"$gte": 100}, "seller_response_count": 0}',
    actions: '{"decision": "refund", "reason": "商家超时未响应", "seller_score_penalty": 2}',
    isActive: true,
    version: 1
  },
  {
    id: 5,
    code: 'RULE_005',
    name: '商家服务分低于阈值',
    category: 'seller_score',
    priority: 70,
    weight: 75,
    description: '商家服务分低于70分，增加买家胜诉权重',
    conditions: '{"seller_service_score": {"$lt": 70}}',
    actions: '{"weight_adjust": 20, "reason": "商家服务分过低"}',
    isActive: false,
    version: 2
  }
])

const getCategoryText = (category) => {
  const map = {
    refund: '退款退货',
    quality: '质量问题',
    advertising: '虚假宣传',
    logistics: '物流问题',
    service: '服务问题',
    seller_score: '商家评分',
    buyer_credit: '买家信誉',
    sla: 'SLA时效'
  }
  return map[category] || category
}

const getCategoryTag = (category) => {
  const map = {
    refund: 'primary',
    quality: 'success',
    advertising: 'warning',
    logistics: 'info',
    service: 'danger',
    seller_score: 'warning',
    buyer_credit: 'primary',
    sla: 'danger'
  }
  return map[category] || 'info'
}

const handleSearch = () => {
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 500)
}

const handleReset = () => {
  Object.assign(searchForm, {
    category: '',
    isActive: null
  })
}

const handleSizeChange = (val) => {
  pagination.pageSize = val
}

const handleCurrentChange = (val) => {
  pagination.page = val
}

const toggleRuleStatus = (row) => {
  ElMessage.success(`规则已${row.isActive ? '启用' : '禁用'}`)
}

const viewRule = (row) => {
  currentRule.value = row
  showViewDialog.value = true
}

const editRule = (row) => {
  isEdit.value = true
  Object.assign(ruleForm, row)
  showCreateDialog.value = true
}

const testRule = (row) => {
  currentRule.value = row
  testData.value = JSON.stringify({
    ticket: {
      type: 'refund',
      category: 'quality',
      days_since_receive: 5,
      seller_service_score: 85
    },
    evidences: [
      { id: 1, type: 'image', analysis: { image_analysis: { has_issue: true } } }
    ]
  }, null, 2)
  testResult.value = null
  showTestDialog.value = true
}

const saveRule = () => {
  saving.value = true
  setTimeout(() => {
    saving.value = false
    showCreateDialog.value = false
    ElMessage.success(isEdit.value ? '规则更新成功' : '规则创建成功')
  }, 1000)
}

const runTest = () => {
  testing.value = true
  setTimeout(() => {
    testing.value = false
    testResult.value = {
      ruleName: currentRule.value?.name,
      passed: Math.random() > 0.5,
      message: '条件匹配，规则将被触发执行'
    }
  }, 1000)
}
</script>

<style scoped>
.rules-page {
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

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
