<template>
  <section class="page" data-module="plank">
    <header class="page-head">
      <div>
        <h2>厂站信息管理</h2>
        <p class="page-desc">
          运行状态按「待投运 → 正常运行 → 停运检修」顺序流转，可退回待投运或退役归档；
          处理工艺、服务区域须退回待投运后才能修改，每次变更都记录时间与经办人。
        </p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记厂站</button>
        <button class="btn" type="button" @click="exportRows">导出厂站信息清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label class="filter-item">
        <span>厂站编号</span>
        <input v-model="filters.keyword" placeholder="按厂站编号检索" />
      </label>
      <label class="filter-item">
        <span>运行状态</span>
        <select v-model="filters.status">
          <option value="">全部状态</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
        </select>
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
          <th>可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td>{{ row['厂站编号'] }}</td>
          <td>{{ row['厂站名称'] }}</td>
          <td>{{ row['设计规模'] }}</td>
          <td>{{ row['处理工艺'] || '—' }}</td>
          <td>{{ row['服务区域'] || '—' }}</td>
          <td>{{ row['投运日期'] || '—' }}</td>
          <td><span class="status-tag" :class="statusClass(row['运行状态'])">{{ row['运行状态'] }}</span></td>
          <td>{{ row['最近经办人'] || '—' }}</td>
          <td>{{ row['最近时间'] || '—' }}</td>
          <td class="row-actions">
            <button class="link" type="button" @click="openDetail(row)">详情</button>
            <template v-if="row['运行状态'] !== '已退役'">
              <button class="link" type="button" @click="openEdit(row)">编辑资料</button>
              <button
                v-for="action in actionsFor(row['运行状态'])"
                :key="action"
                class="link"
                type="button"
                @click="openAction(action, row)"
              >
                {{ action }}
              </button>
            </template>
            <span v-else class="locked-hint">已退役，不可变更</span>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + 1" class="empty-state">暂无厂站信息数据，可先登记厂站</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条厂站信息记录</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
      <span v-else-if="noticeMessage" class="notice-text">{{ noticeMessage }}</span>
    </footer>

    <!-- 登记厂站 -->
    <div v-if="createVisible" class="modal-mask" @click.self="createVisible = false">
      <div class="modal">
        <h3>登记厂站</h3>
        <p class="modal-desc">厂站编号、厂站名称、设计规模为必填；登记后状态为「待投运」。</p>
        <div class="form-grid">
          <label v-for="field in createFields" :key="field.name" class="form-item">
            <span>{{ field.name }}<em v-if="field.required" class="required">*</em></span>
            <input v-model="createForm[field.name]" :placeholder="field.placeholder" />
          </label>
          <label class="form-item">
            <span>经办人<em class="required">*</em></span>
            <input v-model="createForm['经办人']" placeholder="本次登记经办人" />
          </label>
        </div>
        <p v-if="dialogError" class="error-text">{{ dialogError }}</p>
        <div class="modal-actions">
          <button class="btn ghost" type="button" @click="createVisible = false">取消</button>
          <button class="btn primary" type="button" @click="submitCreate">保存登记</button>
        </div>
      </div>
    </div>

    <!-- 状态流转 -->
    <div v-if="actionDialog.visible" class="modal-mask" @click.self="actionDialog.visible = false">
      <div class="modal">
        <h3>{{ actionDialog.action }} · {{ actionDialog.code }}</h3>
        <p class="modal-desc">
          当前状态「{{ actionDialog.status }}」，执行后进入「{{ actionTarget }}」。
          <template v-if="actionDialog.action === '退回待投运'">退回必须写清原因，供后续交接追溯。</template>
          <template v-else-if="actionDialog.action === '退役'">退役后厂站归档，任何变更都会被拒绝。</template>
        </p>
        <label class="form-item">
          <span>经办人<em class="required">*</em></span>
          <input v-model="actionDialog.operator" placeholder="本次操作经办人" />
        </label>
        <label class="form-item">
          <span>原因说明<em v-if="actionDialog.action === '退回待投运'" class="required">*</em></span>
          <textarea v-model="actionDialog.reason" rows="3" placeholder="请写明本次流转的原因"></textarea>
        </label>
        <p v-if="dialogError" class="error-text">{{ dialogError }}</p>
        <div class="modal-actions">
          <button class="btn ghost" type="button" @click="actionDialog.visible = false">取消</button>
          <button class="btn primary" type="button" @click="submitAction">确认{{ actionDialog.action }}</button>
        </div>
      </div>
    </div>

    <!-- 编辑资料 -->
    <div v-if="editDialog.visible" class="modal-mask" @click.self="editDialog.visible = false">
      <div class="modal">
        <h3>编辑资料 · {{ editDialog.code }}</h3>
        <p class="modal-desc">
          当前状态「{{ editDialog.status }}」。
          <template v-if="editDialog.status !== '待投运'">
            处理工艺、服务区域已锁定，需先「退回待投运」并写明原因后才能修改。
          </template>
        </p>
        <div class="form-grid">
          <label class="form-item">
            <span>厂站编号</span>
            <input :value="editDialog.code" disabled />
          </label>
          <label v-for="field in editFields" :key="field" class="form-item">
            <span>
              {{ field }}<em v-if="field === '设计规模'" class="required">*</em>
              <em v-if="isProcessField(field) && editDialog.status !== '待投运'" class="locked">（已锁定）</em>
            </span>
            <input
              v-model="editDialog.form[field]"
              :disabled="isProcessField(field) && editDialog.status !== '待投运'"
            />
          </label>
          <label class="form-item">
            <span>经办人<em class="required">*</em></span>
            <input v-model="editDialog.operator" placeholder="本次修改经办人" />
          </label>
        </div>
        <p v-if="dialogError" class="error-text">{{ dialogError }}</p>
        <div class="modal-actions">
          <button class="btn ghost" type="button" @click="editDialog.visible = false">取消</button>
          <button class="btn primary" type="button" @click="submitEdit">保存修改</button>
        </div>
      </div>
    </div>

    <!-- 厂站详情 -->
    <div v-if="detailDialog.visible" class="modal-mask" @click.self="detailDialog.visible = false">
      <div class="modal wide">
        <h3>厂站详情 · {{ detailDialog.entry?.['厂站编号'] }}</h3>
        <div v-if="detailDialog.entry" class="detail-grid">
          <div v-for="field in detailFields" :key="field" class="detail-item">
            <span class="detail-label">{{ field }}</span>
            <span>{{ detailDialog.entry[field] || '—' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">运行状态</span>
            <span class="status-tag" :class="statusClass(detailDialog.entry['运行状态'])">
              {{ detailDialog.entry['运行状态'] }}
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">最近处理</span>
            <span>
              {{ detailDialog.entry['最近动作'] || '—' }} ·
              {{ detailDialog.entry['最近经办人'] || '—' }} ·
              {{ detailDialog.entry['最近时间'] || '—' }}
            </span>
          </div>
        </div>
        <h4>流转历史（{{ detailDialog.entry?.history?.length ?? 0 }} 条）</h4>
        <table class="data-table history-table">
          <thead>
            <tr>
              <th>#</th><th>时间</th><th>经办人</th><th>动作</th><th>状态变化</th><th>原因 / 变更说明</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in detailDialog.entry?.history ?? []" :key="record.seq">
              <td>{{ record.seq }}</td>
              <td>{{ record.time }}</td>
              <td>{{ record.operator }}</td>
              <td>{{ record.action }}</td>
              <td>{{ record.from ? `${record.from} → ${record.to}` : record.to }}</td>
              <td>{{ record.reason || '—' }}</td>
            </tr>
          </tbody>
        </table>
        <div class="modal-actions">
          <button class="btn" type="button" @click="detailDialog.visible = false">关闭</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { request } from '@/api/client'
import { useSessionStore } from '@/stores/session'

interface HistoryRecord {
  seq: number
  time: string
  operator: string
  action: string
  from: string
  to: string
  reason: string
}

type Row = Record<string, string | number | null> & {
  id: number
  history?: HistoryRecord[]
}

const ENDPOINT = '/api/plank'
const session = useSessionStore()

const statuses = ['待投运', '正常运行', '停运检修', '已退役']
const columns = ['厂站编号', '厂站名称', '设计规模', '处理工艺', '服务区域', '投运日期', '运行状态', '最近经办人', '最近时间']
const detailFields = ['厂站编号', '厂站名称', '设计规模', '排放标准', '处理工艺', '服务区域', '投运日期']
const editFields = ['厂站名称', '设计规模', '排放标准', '处理工艺', '服务区域', '投运日期']
const processFields = ['处理工艺', '服务区域']
const createFields = [
  { name: '厂站编号', required: true, placeholder: '如 PLAN-0005，登记后不可修改' },
  { name: '厂站名称', required: true, placeholder: '如 西区水质净化厂' },
  { name: '设计规模', required: true, placeholder: '如 5万m³/d' },
  { name: '排放标准', required: false, placeholder: '如 一级A' },
  { name: '处理工艺', required: false, placeholder: '如 AAO+深度处理' },
  { name: '服务区域', required: false, placeholder: '如 西区街道' },
  { name: '投运日期', required: false, placeholder: '如 2026-10-01，可留空' },
]

// 每个状态下允许执行的流转动作，与后端 ALLOWED_TRANSITIONS 保持一致。
const ACTION_MAP: Record<string, string[]> = {
  待投运: ['投运'],
  正常运行: ['停运检修', '退回待投运', '退役'],
  停运检修: ['恢复运行', '退回待投运', '退役'],
  已退役: [],
}
const ACTION_TARGET: Record<string, string> = {
  投运: '正常运行',
  停运检修: '停运检修',
  恢复运行: '正常运行',
  退回待投运: '待投运',
  退役: '已退役',
}

const rows = ref<Row[]>([])
const total = ref(0)
const errorMessage = ref('')
const noticeMessage = ref('')
const dialogError = ref('')
const filters = reactive({ keyword: '', status: '' })

const createVisible = ref(false)
const createForm = reactive<Record<string, string>>({})

const actionDialog = reactive({
  visible: false,
  id: 0,
  code: '',
  status: '',
  action: '',
  operator: '',
  reason: '',
})

const editDialog = reactive({
  visible: false,
  id: 0,
  code: '',
  status: '',
  operator: '',
  form: {} as Record<string, string>,
})

const detailDialog = reactive({
  visible: false,
  entry: null as Row | null,
})

const stats = computed(() => {
  const count = (status: string) => rows.value.filter((row) => row['运行状态'] === status).length
  return [
    { label: '待投运厂站', value: count('待投运') },
    { label: '正常运行厂站', value: count('正常运行') },
    { label: '停运检修厂站', value: count('停运检修') },
    { label: '已退役厂站', value: count('已退役') },
  ]
})

const actionTarget = computed(() => ACTION_TARGET[actionDialog.action] ?? '')

function actionsFor(status: unknown): string[] {
  return ACTION_MAP[String(status)] ?? []
}

function isProcessField(field: string): boolean {
  return processFields.includes(field)
}

function statusClass(status: unknown): string {
  const map: Record<string, string> = {
    待投运: 'is-pending',
    正常运行: 'is-running',
    停运检修: 'is-overhaul',
    已退役: 'is-retired',
  }
  return map[String(status)] ?? ''
}

function resetFilters() {
  filters.keyword = ''
  filters.status = ''
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  dialogError.value = ''
  for (const field of createFields) {
    createForm[field.name] = ''
  }
  createForm['经办人'] = session.operator
  createVisible.value = true
}

async function submitCreate() {
  dialogError.value = ''
  const values: Record<string, string> = {}
  for (const field of createFields) {
    values[field.name] = (createForm[field.name] ?? '').trim()
  }
  const result = await postAction(ENDPOINT, {
    values,
    operator: (createForm['经办人'] ?? '').trim(),
  })
  if (!result) return
  createVisible.value = false
  noticeMessage.value = result
  await reload()
}

function openAction(action: string, row: Row) {
  dialogError.value = ''
  actionDialog.id = Number(row.id)
  actionDialog.code = String(row['厂站编号'] ?? '')
  actionDialog.status = String(row['运行状态'] ?? '')
  actionDialog.action = action
  actionDialog.operator = session.operator
  actionDialog.reason = ''
  actionDialog.visible = true
}

async function submitAction() {
  dialogError.value = ''
  const result = await postAction(`${ENDPOINT}/${actionDialog.id}/actions`, {
    values: { action: actionDialog.action },
    operator: actionDialog.operator.trim(),
    reason: actionDialog.reason.trim(),
  })
  if (!result) return
  actionDialog.visible = false
  noticeMessage.value = result
  await reload()
}

function openEdit(row: Row) {
  dialogError.value = ''
  editDialog.id = Number(row.id)
  editDialog.code = String(row['厂站编号'] ?? '')
  editDialog.status = String(row['运行状态'] ?? '')
  editDialog.operator = session.operator
  editDialog.form = {}
  for (const field of editFields) {
    editDialog.form[field] = String(row[field] ?? '')
  }
  editDialog.visible = true
}

async function submitEdit() {
  dialogError.value = ''
  const values: Record<string, string> = {}
  for (const field of editFields) {
    values[field] = (editDialog.form[field] ?? '').trim()
  }
  const response = await request(`${ENDPOINT}/${editDialog.id}`, {
    method: 'PATCH',
    body: JSON.stringify({ values, operator: editDialog.operator.trim() }),
  })
  const payload = (await response.json()) as { ok: boolean; message: string }
  if (!response.ok || !payload.ok) {
    dialogError.value = payload.message || '资料修改未生效，请检查后重试'
    return
  }
  editDialog.visible = false
  noticeMessage.value = payload.message
  await reload()
}

async function openDetail(row: Row) {
  errorMessage.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}`)
    if (!response.ok) {
      throw new Error('厂站详情读取失败')
    }
    detailDialog.entry = (await response.json()) as Row
    detailDialog.visible = true
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '厂站详情读取失败'
  }
}

/** 统一提交动作类请求：失败时把后端说明原样留在弹窗里。 */
async function postAction(url: string, body: Record<string, unknown>): Promise<string | null> {
  try {
    const response = await request(url, {
      method: 'POST',
      body: JSON.stringify(body),
    })
    const payload = (await response.json()) as { ok: boolean; message: string }
    if (!response.ok || !payload.ok) {
      dialogError.value = payload.message || '操作未生效，请检查后重试'
      return null
    }
    return payload.message
  } catch (error) {
    dialogError.value = error instanceof Error ? error.message : '操作失败，请稍后重试'
    return null
  }
}

async function reload() {
  errorMessage.value = ''
  const query = new URLSearchParams()
  if (filters.keyword.trim()) query.set('keyword', filters.keyword.trim())
  if (filters.status) query.set('status', filters.status)
  try {
    const response = await request(`${ENDPOINT}?${query.toString()}`)
    if (!response.ok) {
      throw new Error('厂站列表读取失败')
    }
    const payload = (await response.json()) as { items?: Row[]; total?: number }
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '厂站信息列表读取失败'
  }
}

onMounted(reload)
</script>
