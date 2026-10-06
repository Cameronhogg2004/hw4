// Fortnite-style loot rarity, assigned from price tier.
export type Rarity = 'uncommon' | 'rare' | 'epic' | 'legendary'

export function rarityFor(price: number): Rarity {
  if (price >= 88) return 'legendary'
  if (price >= 68) return 'epic'
  if (price >= 58) return 'rare'
  return 'uncommon'
}

export const formatPrice = (price: number) => `$${price.toFixed(2)}`
