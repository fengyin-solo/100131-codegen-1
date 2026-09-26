<template>
  <section class="page" data-module="plank">
    <header class="page-head">
      <div>
        <h2>厂站信息管理</h2>
        <p class="page-desc">运行状态按待投运 → 正常运行 → 停运检修流转，每次变更都记录时间与经办人，可回溯。</p>
      </div>
      <div class="page-actions">
        <button class="btn primary" type="button" @click="openCreate">登记污水处理厂</button>
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
          <option v-for="status in statuses" :key="status" :value="status">{{ status }}</option>
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
          <td v-for="column in columns" :key="column">
            <span v-if="column === '运行状态'" class="status-tag" :class="statusClass(row[column])">
              {{ row[column] ?? '—' }}
            </span>
            <template v-else>{{ row[column] ?? '—' }}</template>
          </td>
          <td class="row-actions">
            <button class="link" type="button" @click="openDetail(row)">详情</button>
            <template v-if="availableActions(row).length">
              <button
                v-for="action in availableActions(row)"
                :key="action"
                class="link"
                type="button"
                @click="openAction(action, row)"
              >
                {{ action }}
              </button>
            </template>
            <span v-else class="hint-text">已退役，不可改动</span>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="columns.length + 1" class="empty-state">暂无厂站信息数据，可先登记污水处理厂</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条厂站信息记录</span>
      <span v-if="noticeMessage" class="ok-text">{{ noticeMessage }}</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>

    <div v-if="showCreate" class="dialog-mask" @click.self="showCreate = false">
      <div class="dialog">
        <h3>登记污水处理厂</h3>
        <div class="form-grid">
          <label v-for="field in createFields" :key="field.name" class="form-item" :class="{ full: field.full }">
            <span>{{ field.label }}<em v-if="field.required" class="required-mark">*</em></span>
            <input
              v-model="createForm[field.name]"
              :type="field.type ?? 'text'"
              :placeholder="field.required ? `必填，请输入${field.label}` : `选填，请输入${field.label}`"
            />
          </label>
          <label class="form-item">
            <span>经办人<em class="required-mark">*</em></span>
            <input v-model="createForm.经办人" placeholder="登记人姓名" />
          </label>
        </div>
        <p v-if="createError" class="error-text">{{ createError }}</p>
        <div class="dialog-actions">
          <button class="btn ghost" type="button" @click="showCreate = false">取消</button>
          <button class="btn primary" type="button" @click="submitCreate">保存登记</button>
        </div>
      </div>
    </div>

    <div v-if="actionDialog" class="dialog-mask" @click.self="actionDialog = null">
      <div class="dialog">
        <h3>{{ actionDialog.action }} · {{ actionDialog.row.厂站编号 }}</h3>
        <p class="hint-text">
          当前状态「{{ actionDialog.row.运行状态 }}」，执行后变为「{{ actionTarget }}」，变更会记入流转记录。
        </p>
        <div class="form-grid">
          <label class="form-item">
            <span>经办人<em class="required-mark">*</em></span>
            <input v-model="actionOperator" placeholder="经办人姓名" />
          </label>
          <label class="form-item full">
            <span>原因<em v-if="reasonRequired" class="required-mark">*（退回待投运必须写清原因）</em></span>
            <textarea v-model="actionReason" rows="3" :placeholder="reasonRequired ? '必填，说明退回原因' : '选填，补充说明本次操作'"></textarea>
          </label>
        </div>
        <p v-if="actionError" class="error-text">{{ actionError }}</p>
        <div class="dialog-actions">
          <button class="btn ghost" type="button" @click="actionDialog = null">取消</button>
          <button class="btn primary" type="button" @click="submitAction">确认执行</button>
        </div>
      </div>
    </div>

    <div v-if="detail" class="dialog-mask" @click.self="detail = null">
      <div class="dialog wide">
        <h3>
          厂站详情 · {{ detail.厂站编号 }}
          <span class="status-tag" :class="statusClass(detail.运行状态)">{{ detail.运行状态 }}</span>
        </h3>
        <p v-if="lastHandler" class="hint-text">
          最近处理：{{ lastHandler.经办人 }} · {{ lastHandler.时间 }} · {{ lastHandler.动作 }}（交接后刷新仍可查看）
        </p>
        <dl class="detail-grid">
          <div v-for="column in columns" :key="column">
            <dt>{{ column }}</dt>
            <dd>{{ detail[column] ?? '—' }}</dd>
          </div>
        </dl>

        <h4 class="section-title">资料变更（处理工艺 / 服务区域）</h4>
        <p v-if="!canEditDetail" class="hint-text">
          {{ detail.运行状态 === '已退役' ? '厂站已退役，不能再改动。' : '仅「待投运」状态可修改，请先在列表中执行「退回待投运」并写清原因。' }}
        </p>
        <div class="form-grid">
          <label class="form-item">
            <span>处理工艺</span>
            <input v-model="editForm.处理工艺" :disabled="!canEditDetail" />
          </label>
          <label class="form-item">
            <span>服务区域</span>
            <input v-model="editForm.服务区域" :disabled="!canEditDetail" />
          </label>
          <label class="form-item">
            <span>经办人<em class="required-mark">*</em></span>
            <input v-model="editForm.经办人" :disabled="!canEditDetail" />
          </label>
          <label class="form-item">
            <span>变更原因<em class="required-mark">*</em></span>
            <input v-model="editForm.原因" :disabled="!canEditDetail" placeholder="必填，说明为什么改" />
          </label>
        </div>
        <p v-if="editError" class="error-text">{{ editError }}</p>
        <p v-if="editNotice" class="ok-text">{{ editNotice }}</p>
        <div v-if="canEditDetail" class="dialog-actions">
          <button class="btn primary" type="button" @click="submitEdit">提交资料变更</button>
        </div>

        <h4 class="section-title">流转记录（共 {{ history.length }} 次）</h4>
        <table class="data-table">
          <thead>
            <tr><th>时间</th><th>经办人</th><th>动作</th><th>状态变化</th><th>变更内容</th><th>原因</th></tr>
          </thead>
          <tbody>
            <tr v-for="(record, index) in history" :key="index">
              <td>{{ record.时间 }}</td>
              <td>{{ record.经办人 }}</td>
              <td>{{ record.动作 }}</td>
              <td>{{ record.原状态 ? `${record.原状态} → ${record.新状态}` : record.新状态 }}</td>
              <td>{{ record.内容 || '—' }}</td>
              <td>{{ record.原因 || '—' }}</td>
            </tr>
            <tr v-if="!history.length">
              <td colspan="6" class="empty-state">暂无流转记录</td>
            </tr>
          </tbody>
        </table>
        <div class="dialog-actions">
          <button class="btn ghost" type="button" @click="detail = null">关闭</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { request } from '@/api/client'
import { useSessionStore } from '@/stores/session'

type HistoryEntry = {
  时间: string
  经办人: string
  动作: string
  原状态: string
  新状态: string
  原因: string
  内容: string
}
type Row = Record<string, any> & { id: number; 流转记录?: HistoryEntry[] }
type ActionResponse = { ok: boolean; message: string; entry?: Row }

const ENDPOINT = '/api/plank'
const columns = ['厂站编号', '厂站名称', '设计规模', '排放标准', '处理工艺', '服务区域', '投运日期', '运行状态']
const statuses = ['待投运', '正常运行', '停运检修', '已退役']
const ACTIONS_BY_STATUS: Record<string, string[]> = {
  待投运: ['申请投运', '退役'],
  正常运行: ['停运检修', '退回待投运'],
  停运检修: ['恢复运行', '退回待投运', '退役'],
  已退役: [],
}
const ACTION_TARGETS: Record<string, string> = {
  申请投运: '正常运行',
  停运检修: '停运检修',
  恢复运行: '正常运行',
  退回待投运: '待投运',
  退役: '已退役',
}
type CreateField = { name: string; label: string; required: boolean; type?: string; full?: boolean }
const createFields: CreateField[] = [
  { name: '厂站编号', label: '厂站编号', required: true },
  { name: '厂站名称', label: '厂站名称', required: true },
  { name: '设计规模', label: '设计规模', required: true },
  { name: '排放标准', label: '排放标准', required: false },
  { name: '处理工艺', label: '处理工艺', required: false },
  { name: '服务区域', label: '服务区域', required: false },
  { name: '投运日期', label: '投运日期', required: false, type: 'date', full: true },
]

const session = useSessionStore()

const rows = ref<Row[]>([])
const total = ref(0)
const summary = ref<Record<string, number>>({})
const errorMessage = ref('')
const noticeMessage = ref('')
const filters = ref({ keyword: '', status: '' })

const showCreate = ref(false)
const createForm = ref<Record<string, string>>({})
const createError = ref('')

const actionDialog = ref<{ action: string; row: Row } | null>(null)
const actionOperator = ref('')
const actionReason = ref('')
const actionError = ref('')

const detail = ref<Row | null>(null)
const editForm = ref({ 处理工艺: '', 服务区域: '', 原因: '', 经办人: '' })
const editError = ref('')
const editNotice = ref('')

const stats = computed(() => statuses.map((status) => ({ label: `${status}厂站`, value: summary.value[status] ?? 0 })))
const reasonRequired = computed(() => actionDialog.value?.action === '退回待投运')
const actionTarget = computed(() => (actionDialog.value ? ACTION_TARGETS[actionDialog.value.action] : ''))
const history = computed<HistoryEntry[]>(() => [...(detail.value?.流转记录 ?? [])].reverse())
const lastHandler = computed<HistoryEntry | null>(() => history.value[0] ?? null)
const canEditDetail = computed(() => detail.value?.status === '待投运')

function statusClass(status: unknown) {
  return {
    'st-pending': status === '待投运',
    'st-running': status === '正常运行',
    'st-maint': status === '停运检修',
    'st-retired': status === '已退役',
  }
}

function availableActions(row: Row) {
  return ACTIONS_BY_STATUS[String(row.status ?? '')] ?? []
}

function resetFilters() {
  filters.value = { keyword: '', status: '' }
  void reload()
}

function exportRows() {
  window.open(`${ENDPOINT}/export`, '_blank')
}

function openCreate() {
  createForm.value = { 经办人: session.operator }
  createError.value = ''
  showCreate.value = true
}

function openAction(action: string, row: Row) {
  actionDialog.value = { action, row }
  actionOperator.value = session.operator
  actionReason.value = ''
  actionError.value = ''
}

async function send(url: string, method: string, body: unknown): Promise<ActionResponse> {
  const response = await request(url, { method, body: JSON.stringify(body) })
  const payload = (await response.json().catch(() => null)) as (ActionResponse & { detail?: string }) | null
  if (!response.ok) {
    throw new Error(payload?.detail ?? `接口返回 ${response.status}，操作未生效`)
  }
  if (!payload) {
    throw new Error('接口未返回有效内容，操作未生效')
  }
  return payload
}

async function submitCreate() {
  createError.value = ''
  try {
    const payload = await send(ENDPOINT, 'POST', { values: { ...createForm.value } })
    if (!payload.ok) {
      createError.value = payload.message
      return
    }
    session.setOperator(createForm.value.经办人 ?? '')
    showCreate.value = false
    noticeMessage.value = payload.message
    await reload()
  } catch (error) {
    createError.value = error instanceof Error ? error.message : '厂站信息登记失败'
  }
}

async function submitAction() {
  if (!actionDialog.value) return
  actionError.value = ''
  const { action, row } = actionDialog.value
  try {
    const payload = await send(`${ENDPOINT}/${row.id}/actions`, 'POST', {
      values: { action, 经办人: actionOperator.value, 原因: actionReason.value },
    })
    if (!payload.ok) {
      actionError.value = payload.message
      return
    }
    session.setOperator(actionOperator.value)
    actionDialog.value = null
    noticeMessage.value = payload.message
    await reload()
    if (detail.value?.id === row.id) {
      await openDetail(row)
    }
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : '厂站信息操作失败'
  }
}

async function openDetail(row: Row) {
  editError.value = ''
  editNotice.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}`)
    const payload = await response.json().catch(() => null)
    if (!response.ok) {
      throw new Error(payload?.detail ?? '厂站详情读取失败')
    }
    detail.value = payload as Row
    editForm.value = {
      处理工艺: String(payload.处理工艺 ?? ''),
      服务区域: String(payload.服务区域 ?? ''),
      原因: '',
      经办人: session.operator,
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '厂站详情读取失败'
  }
}

async function submitEdit() {
  if (!detail.value) return
  editError.value = ''
  editNotice.value = ''
  try {
    const payload = await send(`${ENDPOINT}/${detail.value.id}`, 'PUT', { values: { ...editForm.value } })
    if (!payload.ok) {
      editError.value = payload.message
      return
    }
    session.setOperator(editForm.value.经办人)
    editNotice.value = payload.message
    await reload()
    await openDetail(detail.value)
    editNotice.value = payload.message
  } catch (error) {
    editError.value = error instanceof Error ? error.message : '资料变更失败'
  }
}

async function reload() {
  errorMessage.value = ''
  const query = new URLSearchParams()
  if (filters.value.keyword.trim()) query.set('keyword', filters.value.keyword.trim())
  if (filters.value.status) query.set('status', filters.value.status)
  try {
    const [listResponse, summaryResponse] = await Promise.all([
      request(`${ENDPOINT}?${query.toString()}`),
      request(`${ENDPOINT}/summary`),
    ])
    if (!listResponse.ok) {
      throw new Error('污水处理厂列表读取失败')
    }
    const payload = await listResponse.json()
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
    if (summaryResponse.ok) {
      summary.value = await summaryResponse.json()
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '厂站信息列表读取失败'
  }
}

onMounted(reload)
</script>
