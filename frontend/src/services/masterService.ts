import { api } from "./api"
import type {
  Customer,
  Supplier,
  Product,
  RawMaterial,
  PackagingItem,
  PriceList,
  PriceListItem,
  EffectivePrice,
  UnitConversionResult,
} from "../types/masters"

export const masterService = {
  // Customers
  async getCustomers(params?: { search?: string; customer_type?: string; state?: string; is_active?: boolean }): Promise<Customer[]> {
    const res = await api.get<Customer[]>("/customers", { params })
    return res.data
  },
  async getCustomer(id: string): Promise<Customer> {
    const res = await api.get<Customer>(`/customers/${id}`)
    return res.data
  },
  async createCustomer(data: Partial<Customer>): Promise<Customer> {
    const res = await api.post<Customer>("/customers", data)
    return res.data
  },
  async updateCustomer(id: string, data: Partial<Customer>): Promise<Customer> {
    const res = await api.patch<Customer>(`/customers/${id}`, data)
    return res.data
  },
  async deleteCustomer(id: string): Promise<Customer> {
    const res = await api.delete<Customer>(`/customers/${id}`)
    return res.data
  },

  // Suppliers
  async getSuppliers(params?: { search?: string; is_active?: boolean }): Promise<Supplier[]> {
    const res = await api.get<Supplier[]>("/suppliers", { params })
    return res.data
  },
  async createSupplier(data: Partial<Supplier>): Promise<Supplier> {
    const res = await api.post<Supplier>("/suppliers", data)
    return res.data
  },
  async updateSupplier(id: string, data: Partial<Supplier>): Promise<Supplier> {
    const res = await api.patch<Supplier>(`/suppliers/${id}`, data)
    return res.data
  },
  async deleteSupplier(id: string): Promise<Supplier> {
    const res = await api.delete<Supplier>(`/suppliers/${id}`)
    return res.data
  },

  // Products
  async getProducts(params?: { search?: string; category?: string; is_active?: boolean }): Promise<Product[]> {
    const res = await api.get<Product[]>("/products", { params })
    return res.data
  },
  async createProduct(data: Partial<Product>): Promise<Product> {
    const res = await api.post<Product>("/products", data)
    return res.data
  },
  async updateProduct(id: string, data: Partial<Product>): Promise<Product> {
    const res = await api.patch<Product>(`/products/${id}`, data)
    return res.data
  },
  async deleteProduct(id: string): Promise<Product> {
    const res = await api.delete<Product>(`/products/${id}`)
    return res.data
  },

  // Raw Materials
  async getRawMaterials(params?: { search?: string; category?: string; is_active?: boolean }): Promise<RawMaterial[]> {
    const res = await api.get<RawMaterial[]>("/raw-materials", { params })
    return res.data
  },
  async createRawMaterial(data: Partial<RawMaterial>): Promise<RawMaterial> {
    const res = await api.post<RawMaterial>("/raw-materials", data)
    return res.data
  },
  async updateRawMaterial(id: string, data: Partial<RawMaterial>): Promise<RawMaterial> {
    const res = await api.patch<RawMaterial>(`/raw-materials/${id}`, data)
    return res.data
  },

  // Packaging
  async getPackaging(params?: { search?: string; category?: string; is_active?: boolean }): Promise<PackagingItem[]> {
    const res = await api.get<PackagingItem[]>("/packaging", { params })
    return res.data
  },
  async createPackaging(data: Partial<PackagingItem>): Promise<PackagingItem> {
    const res = await api.post<PackagingItem>("/packaging", data)
    return res.data
  },
  async updatePackaging(id: string, data: Partial<PackagingItem>): Promise<PackagingItem> {
    const res = await api.patch<PackagingItem>(`/packaging/${id}`, data)
    return res.data
  },

  // Price Lists
  async getPriceLists(params?: { customer_type?: string; is_active?: boolean }): Promise<PriceList[]> {
    const res = await api.get<PriceList[]>("/price-lists", { params })
    return res.data
  },
  async getPriceList(id: string): Promise<PriceList> {
    const res = await api.get<PriceList>(`/price-lists/${id}`)
    return res.data
  },
  async createPriceList(data: Partial<PriceList>): Promise<PriceList> {
    const res = await api.post<PriceList>("/price-lists", data)
    return res.data
  },
  async addPriceListItem(priceListId: string, itemData: Partial<PriceListItem>): Promise<PriceListItem> {
    const res = await api.post<PriceListItem>(`/price-lists/${priceListId}/items`, itemData)
    return res.data
  },
  async getEffectivePrice(customerId: string, productId: string): Promise<EffectivePrice> {
    const res = await api.get<EffectivePrice>("/price-lists/effective-price", {
      params: { customer_id: customerId, product_id: productId },
    })
    return res.data
  },

  // Units
  async convertUnit(data: { quantity: string; from_unit: string; to_unit: string; packets_per_carton?: number }): Promise<UnitConversionResult> {
    const res = await api.post<UnitConversionResult>("/units/convert", data)
    return res.data
  },
  async getSupportedUnits(): Promise<{ categories: Record<string, string[]>; base_units: string[] }> {
    const res = await api.get("/units/supported")
    return res.data
  },
}
