// =============================================================
// Crop and Produce Visual Assets & Metadata (§5.11)
// Single authoritative source of truth for crop metadata,
// authentic photography, local names (hi, mr), and standard units.
// =============================================================

export const CROPS_METADATA = [
  {
    id: 'onion',
    name: 'Onion',
    localImage: '/images/crop-onion.jpeg',
    unit: 'quintal',
    defaultGrade: 'Grade A',
    typicalPriceRange: [2200, 2650],
    commonNames: {
      en: 'Onion',
      hi: 'प्याज',
      mr: 'कांदा',
    },
    popularVarieties: ['Garwa', 'Pol', 'Rangda'],
  },
  {
    id: 'tomato',
    name: 'Tomato',
    localImage: '/images/crop-tomato.webp',
    unit: 'quintal',
    defaultGrade: 'Grade A',
    typicalPriceRange: [1400, 2100],
    commonNames: {
      en: 'Tomato',
      hi: 'टमाटर',
      mr: 'टोमॅटो',
    },
    popularVarieties: ['Abhinav', 'Vaishali', 'Saaho'],
  },
  {
    id: 'wheat',
    name: 'Wheat',
    localImage: '/images/crop-wheat.jpg',
    unit: 'quintal',
    defaultGrade: 'Sharbati',
    typicalPriceRange: [2400, 2850],
    commonNames: {
      en: 'Wheat',
      hi: 'गेहूं',
      mr: 'गहू',
    },
    popularVarieties: ['Lokwan', 'Sharbati', 'Kalyan Sona'],
  },
  {
    id: 'potato',
    name: 'Potato',
    localImage: '/images/crop-potato.jpeg',
    unit: 'quintal',
    defaultGrade: 'Grade A',
    typicalPriceRange: [1200, 1850],
    commonNames: {
      en: 'Potato',
      hi: 'आलू',
      mr: 'बटाटा',
    },
    popularVarieties: ['Kufri Jyoti', 'Kufri Bahar', 'Lal Gulab'],
  },
  {
    id: 'rice',
    name: 'Rice',
    localImage: '/images/crop-rice.jpg',
    unit: 'quintal',
    defaultGrade: 'Kolam',
    typicalPriceRange: [3200, 4200],
    commonNames: {
      en: 'Rice (Paddy)',
      hi: 'चावल (धान)',
      mr: 'तांदूळ (भात)',
    },
    popularVarieties: ['Indrayani', 'Wada Kolam', 'Basmati'],
  },
  {
    id: 'soyabean',
    name: 'Soyabean',
    localImage: '/images/crop-soybean.jpg',
    unit: 'quintal',
    defaultGrade: 'Grade A',
    typicalPriceRange: [4100, 4800],
    commonNames: {
      en: 'Soyabean',
      hi: 'सोयाबीन',
      mr: 'सोयाबीन',
    },
    popularVarieties: ['JS 335', 'JS 9305'],
  },
  {
    id: 'cotton',
    name: 'Cotton',
    localImage: '/images/crop-cotton.jpg',
    unit: 'quintal',
    defaultGrade: 'Medium Staple',
    typicalPriceRange: [6500, 7800],
    commonNames: {
      en: 'Cotton',
      hi: 'कपास',
      mr: 'कापूस',
    },
    popularVarieties: ['Bt Cotton', 'Desi Cotton'],
  },
  {
    id: 'maize',
    name: 'Maize',
    localImage: '/images/crop-maize.svg',
    unit: 'quintal',
    defaultGrade: 'Yellow Feed',
    typicalPriceRange: [1800, 2300],
    commonNames: {
      en: 'Maize',
      hi: 'मक्का',
      mr: 'मका',
    },
    popularVarieties: ['Yellow Maize', 'Sweet Corn'],
  },
  {
    id: 'chilli',
    name: 'Chilli',
    localImage: '/images/crop-chilli.jpg',
    unit: 'quintal',
    defaultGrade: 'Grade A Red',
    typicalPriceRange: [12000, 18000],
    commonNames: {
      en: 'Chilli',
      hi: 'मिर्च',
      mr: 'मिरची',
    },
    popularVarieties: ['Guntur Sanam', 'Byadagi'],
  },
];

// Map lookup by name
export const CROP_IMAGES = CROPS_METADATA.reduce((acc, crop) => {
  acc[crop.name] = crop.localImage;
  return acc;
}, {
  Soybean: '/images/crop-soybean.jpg',
  Soyabean: '/images/crop-soybean.jpg',
});

/**
 * Returns the photographic image path for a given crop name with fallback
 */
export function getCropImage(cropName) {
  if (!cropName) return CROPS_METADATA[0].localImage;
  const raw = String(cropName).toLowerCase().trim();
  const normalized = (raw === 'soybean' || raw === 'soya') ? 'soyabean' : raw;
  const match = CROPS_METADATA.find(
    (c) => c.name.toLowerCase() === normalized || c.id.toLowerCase() === normalized
  );
  return match ? match.localImage : CROPS_METADATA[0].localImage;
}

/**
 * Returns full metadata record for a given crop name
 */
export function getCropMetadata(cropName) {
  if (!cropName) return CROPS_METADATA[0];
  const raw = String(cropName).toLowerCase().trim();
  const normalized = (raw === 'soybean' || raw === 'soya') ? 'soyabean' : raw;
  const match = CROPS_METADATA.find(
    (c) => c.name.toLowerCase() === normalized || c.id.toLowerCase() === normalized
  );
  return match || {
    id: String(cropName).toLowerCase(),
    name: cropName,
    localImage: '/images/crop-wheat.jpg',
    unit: 'quintal',
    defaultGrade: 'Grade A',
    typicalPriceRange: [2000, 3000],
    commonNames: { en: cropName, hi: cropName, mr: cropName },
    popularVarieties: [],
  };
}

/**
 * Returns localized name for a crop (hi, mr, en)
 */
export function getLocalizedCropName(cropName, lang = 'en') {
  const meta = getCropMetadata(cropName);
  return meta.commonNames?.[lang] || meta.name;
}
