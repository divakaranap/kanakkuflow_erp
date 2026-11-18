import Dexie, { type Table } from 'dexie'

export interface CachedCustomer {
  id: string
  customer_code: string
  customer_name: string
  phone?: string
  gstin?: string
  state_code?: string
  credit_limit_paise: number
}

export interface CachedProduct {
  id: string
  sku: string
  product_name: string
  base_unit: string
  selling_price_paise: number
  gst_rate: number
}

export interface QueuedOrderItem {
  product_id: string
  product_name: string
  ordered_quantity: number
  unit_price_paise?: number
  line_total_paise: number
}

export interface QueuedOrder {
  client_order_uuid: string
  customer_id: string
  customer_name: string
  order_date: string
  delivery_date?: string
  notes?: string
  items: QueuedOrderItem[]
  total_amount_paise: number
  sync_status: 'PENDING' | 'SYNCED' | 'FAILED'
  server_order_id?: string
  server_order_number?: string
  error_message?: string
  created_at: string
}

export class KanakkuflowOfflineDatabase extends Dexie {
  customers!: Table<CachedCustomer, string>
  products!: Table<CachedProduct, string>
  queued_orders!: Table<QueuedOrder, string>

  constructor() {
    super('KanakkuflowOfflineDB')
    this.version(1).stores({
      customers: 'id, customer_code, customer_name',
      products: 'id, sku, product_name',
      queued_orders: 'client_order_uuid, customer_id, sync_status, created_at',
    })
  }
}

export const offlineDb = new KanakkuflowOfflineDatabase()

export const offlineStorage = {
  async cacheMasterData(customers: CachedCustomer[], products: CachedProduct[]): Promise<void> {
    await offlineDb.transaction('rw', [offlineDb.customers, offlineDb.products], async () => {
      await offlineDb.customers.clear()
      await offlineDb.products.clear()
      await offlineDb.customers.bulkPut(customers)
      await offlineDb.products.bulkPut(products)
    })
  },

  async getCachedCustomers(): Promise<CachedCustomer[]> {
    return await offlineDb.customers.toArray()
  },

  async getCachedProducts(): Promise<CachedProduct[]> {
    return await offlineDb.products.toArray()
  },

  async queueOrder(order: Omit<QueuedOrder, 'created_at'>): Promise<void> {
    await offlineDb.queued_orders.put({
      ...order,
      created_at: new Date().toISOString(),
    })
  },

  async getPendingOrders(): Promise<QueuedOrder[]> {
    return await offlineDb.queued_orders
      .where('sync_status')
      .equals('PENDING')
      .toArray()
  },

  async getAllQueuedOrders(): Promise<QueuedOrder[]> {
    return await offlineDb.queued_orders.orderBy('created_at').reverse().toArray()
  },

  async markOrderSynced(
    client_uuid: string,
    server_order_id: string,
    server_order_number: string
  ): Promise<void> {
    await offlineDb.queued_orders.update(client_uuid, {
      sync_status: 'SYNCED',
      server_order_id,
      server_order_number,
      error_message: undefined,
    })
  },

  async markOrderFailed(client_uuid: string, error_message: string): Promise<void> {
    await offlineDb.queued_orders.update(client_uuid, {
      sync_status: 'FAILED',
      error_message,
    })
  },

  async clearSyncedOrders(): Promise<void> {
    await offlineDb.queued_orders
      .where('sync_status')
      .equals('SYNCED')
      .delete()
  },
}
