// Shared storefront helpers: categories, color swatches, stock urgency.
import type { Product } from './api'

export const CATEGORIES = [
  { key: 'all', label: 'All gear' },
  { key: 'hoodies', label: 'Hoodies' },
  { key: 'crewnecks', label: 'Crewnecks' },
  { key: 'tees', label: 'Tees' },
  { key: 'quarter-zips', label: 'Quarter-Zips' },
  { key: 'jackets', label: 'Jackets & Fleece' },
] as const

export const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

export const LOW_STOCK = 15

const SWATCHES: [string, string][] = [
  ['navy', '#1b2a52'],
  ['yale blue', '#00356b'],
  ['royal', '#2453c8'],
  ['light blue', '#8fbbe8'],
  ['blue', '#2f5fb3'],
  ['heather', '#a7a9ad'],
  ['charcoal', '#3d3f44'],
  ['gray', '#8e9196'],
  ['grey', '#8e9196'],
  ['black', '#16171a'],
  ['white', '#f7f7f5'],
  ['cream', '#efe6cf'],
  ['oatmeal', '#d9cdb4'],
  ['red', '#c8243b'],
  ['crimson', '#a51c30'],
  ['maroon', '#6d1f2c'],
  ['green', '#2f7d4c'],
  ['gold', '#d6a62c'],
  ['yellow', '#f2c94c'],
  ['orange', '#e8762d'],
  ['pink', '#f2a5c0'],
  ['purple', '#6b3fa0'],
  ['brown', '#7a5233'],
  ['tan', '#c9a97c'],
]

export function swatch(color: string): string {
  const lowered = color.toLowerCase()
  return SWATCHES.find(([name]) => lowered.includes(name))?.[1] ?? '#9aa0a6'
}

export function stockLabel(p: Pick<Product, 'total_stock'>): string | null {
  if (p.total_stock === 0) return 'Sold out'
  if (p.total_stock <= LOW_STOCK) return `Only ${p.total_stock} left`
  return null
}
