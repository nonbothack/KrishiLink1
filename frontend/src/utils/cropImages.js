// =============================================================
// Crop and Produce Visual Assets Map
// Provides high-quality, authentic agricultural imagery for crops
// =============================================================

export const CROP_IMAGES = {
  Onion: '/images/crop-onion.jpeg',
  Tomato: '/images/crop-tomato.webp',
  Wheat: '/images/crop-wheat.jpg',
  Rice: '/images/crop-rice.jpg',
  Potato: '/images/crop-potato.jpeg',
  Soybean: '/images/crop-soybean.jpg',
  Soyabean: '/images/crop-soybean.jpg',
  Cotton: '/images/crop-cotton.jpg',
  Chilli: '/images/crop-chilli.jpg',
  Maize: '/images/crop-maize.svg',
};

// Fallback icon/image if a crop is not in the map
export const getCropImage = (cropName) => {
  if (!cropName) return CROP_IMAGES.Wheat;
  const s = String(cropName).trim().toLowerCase();
  if (s.includes('soya') || s.includes('soybean')) return CROP_IMAGES.Soybean;
  if (s.includes('cotton') || s.includes('kapas')) return CROP_IMAGES.Cotton;
  if (s.includes('chilli') || s.includes('chili') || s.includes('mirch')) return CROP_IMAGES.Chilli;
  if (s.includes('wheat') || s.includes('gehun') || s.includes('gehu')) return CROP_IMAGES.Wheat;
  if (s.includes('rice') || s.includes('paddy') || s.includes('chawal')) return CROP_IMAGES.Rice;
  if (s.includes('onion') || s.includes('pyaz')) return CROP_IMAGES.Onion;
  if (s.includes('tomato') || s.includes('tamatar')) return CROP_IMAGES.Tomato;
  if (s.includes('potato') || s.includes('aloo')) return CROP_IMAGES.Potato;
  if (s.includes('maize') || s.includes('makka')) return CROP_IMAGES.Maize;

  const normalized = Object.keys(CROP_IMAGES).find(
    (k) => k.toLowerCase() === s
  );
  return normalized ? CROP_IMAGES[normalized] : CROP_IMAGES.Wheat;
};
