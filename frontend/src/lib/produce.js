export const CROPS = ['Onion','Tomato','Soybean','Cotton','Wheat','Potato','Chilli','Rice','Maize'];
export const UNIT_FACTORS = { quintal: 1, kg: 0.01, tonne: 10 };
export function canonicalLot(quantity, price, unit) {
  const factor = UNIT_FACTORS[unit];
  if (!factor || !Number.isFinite(Number(quantity)) || !Number.isFinite(Number(price)) || Number(quantity) <= 0 || Number(price) <= 0) throw new Error('Invalid quantity or price');
  return { quantity: Number((Number(quantity)*factor).toFixed(6)), asking_price: Number((Number(price)/factor).toFixed(2)), unit:'quintal' };
}
export function convertUnit(quantity, price, from, to) {
  return { quantity: quantity === '' ? '' : Number((Number(quantity)*UNIT_FACTORS[from]/UNIT_FACTORS[to]).toFixed(6)), price: price === '' ? '' : Number((Number(price)*UNIT_FACTORS[to]/UNIT_FACTORS[from]).toFixed(2)) };
}
export function dateLabel(value, locale='en') {
  if (!value) return null;
  const normalized = /^\d{2}\/\d{2}\/\d{4}$/.test(value) ? value.split('/').reverse().join('-') : value;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : new Intl.DateTimeFormat(locale+'-IN',{day:'numeric',month:'short',year:'numeric'}).format(date);
}
