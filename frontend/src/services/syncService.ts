import { api } from './api'
import {
  offlineStorage,
  type CachedCustomer,
  type CachedProduct,
  type QueuedOrder,
} from '../lib/offlineDb'

export interface SyncReferenceDataResponse {
  timestamp: string
  customers: CachedCustomer[]
  products: CachedProduct[]
}

export interface SyncedOrderResult {
  client_order_uuid: string
  sales_order_id: string
  order_number: string
  grand_total_paise: number
  status: string
}

export interface FailedOrderResult {
  client_order_uuid: string
  error: string
}

export interface SyncOrdersResponse {
  synced: SyncedOrderResult[]
  failed: FailedOrderResult[]
}

export const syncService = {
  async refreshOfflineReferenceData(): Promise<{ customerCount: number; productCount: number }> {
    const response = await api.get<SyncReferenceDataResponse>('/sync/reference-data')
    const { customers, products } = response.data

    await offlineStorage.cacheMasterData(customers, products)
    return {
      customerCount: customers.length,
      productCount: products.length,
    }
  },

  async syncPendingOrders(): Promise<{ syncedCount: number; failedCount: number }> {
    const pending = await offlineStorage.getPendingOrders()
    if (pending.length === 0) {
      return { syncedCount: 0, failedCount: 0 }
    }

    const payload = {
      orders: pending.map((order) => ({
        client_order_uuid: order.client_order_uuid,
        customer_id: order.customer_id,
        delivery_date: order.delivery_date,
        notes: order.notes,
        items: order.items.map((item) => ({
          product_id: item.product_id,
          ordered_quantity: item.ordered_quantity,
          unit_price_paise: item.unit_price_paise,
        })),
      })),
    }

    const response = await api.post<SyncOrdersResponse>('/sync/orders', payload)
    const { synced, failed } = response.data

    for (const item of synced) {
      await offlineStorage.markOrderSynced(
        item.client_order_uuid,
        item.sales_order_id,
        item.order_number
      )
    }

    for (const item of failed) {
      await offlineStorage.markOrderFailed(item.client_order_uuid, item.error)
    }

    return {
      syncedCount: synced.length,
      failedCount: failed.length,
    }
  },

  async queueAndAttemptSync(order: Omit<QueuedOrder, 'created_at'>): Promise<boolean> {
    // 1. Always write locally first (offline-first design)
    await offlineStorage.queueOrder(order)

    // 2. If online, trigger immediate background sync
    if (navigator.onLine) {
      try {
        await this.syncPendingOrders()
        return true
      } catch (err) {
        console.warn('Online sync failed, order remains safely queued in local offline DB:', err)
        return false
      }
    }
    return false
  },
}
