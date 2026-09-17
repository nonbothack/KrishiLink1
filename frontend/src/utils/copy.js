// Reviewed together by key. Regional language review remains a release requirement.
const rows = {
  brandLine: ['A better way to trade your harvest','तुमच्या शेतमालाच्या व्यापाराचा सोपा मार्ग','आपकी उपज के व्यापार का आसान तरीका'],
  heroTag: ['FROM YOUR FARM. ON YOUR TERMS.','तुमचे शेत. तुमच्या अटी.','आपका खेत। आपकी शर्तें।'],
  heroTitle: ['Your harvest.\nYour next opportunity.','तुमचा शेतमाल.\nतुमची नवी संधी.','आपकी उपज।\nआपका नया अवसर।'],
  heroText: ['Check market prices, list your crop, and compare offers. Take the next step with a clearer picture.','बाजारभाव पाहा, शेतमालाची नोंद करा आणि खरेदीदारांच्या किंमतींची तुलना करा. माहिती घेऊन पुढचे पाऊल टाका.','बाजार भाव देखें, अपनी फसल दर्ज करें और खरीदारों के प्रस्तावों की तुलना करें।'],
  checkPrices: ['Check market prices','बाजारभाव पाहा','बाजार भाव देखें'],
  listCrop: ['List my crop','शेतमाल विक्रीसाठी नोंदवा','अपनी फसल दर्ज करें'],
  buyProduce: ['Buy produce','शेतमाल खरेदी करा','उपज खरीदें'],
  noAccount: ['No account needed to check prices','भाव पाहण्यासाठी खाते लागत नाही','भाव देखने के लिए खाते की जरूरत नहीं'],
  howTitle: ['From harvest to a conversation.','शेतमालापासून खरेदीदारापर्यंत.','फसल से खरीदार तक।'],
  howText: ['Three simple steps to get started.','सुरुवात करण्यासाठी तीन सोप्या पायऱ्या.','शुरू करने के तीन आसान कदम।'],
  step1: ['Know your market','बाजारभाव जाणून घ्या','अपना बाजार जानें'],
  step1Text: ['Compare reported prices by crop and market. Always check the date and unit.','पीक आणि बाजारानुसार भावांची तुलना करा. तारीख आणि एकक नक्की पाहा.','फसल और बाजार के अनुसार भावों की तुलना करें। तारीख और इकाई जरूर देखें।'],
  step2: ['Tell buyers what you have','तुमच्याकडे काय आहे ते सांगा','खरीदारों को अपनी उपज बताएं'],
  step2Text: ['Choose your crop, quantity, location and asking price. Review before publishing.','पीक, प्रमाण, ठिकाण आणि अपेक्षित किंमत भरा. प्रसिद्ध करण्यापूर्वी तपासा.','फसल, मात्रा, स्थान और अपनी कीमत दर्ज करें। प्रकाशित करने से पहले जांचें।'],
  step3: ['Choose your next step','पुढचे पाऊल ठरवा','अगला कदम चुनें'],
  step3Text: ['Read each offer and its total. Accept only when the terms work for you.','प्रत्येक प्रस्ताव आणि एकूण रक्कम वाचा. अटी मान्य असल्यासच स्वीकारा.','हर प्रस्ताव और कुल राशि पढ़ें। शर्तें सही लगने पर ही स्वीकार करें।'],
  together: ['One marketplace. Different ways to grow.','एक बाजारपेठ. प्रगतीचे वेगवेगळे मार्ग.','एक बाजार। बढ़ने के अलग-अलग रास्ते।'],
  farmerRole: ['I grow crops','मी शेती करतो','मैं खेती करता हूं'],
  buyerRole: ['I buy produce','मी शेतमाल खरेदी करतो','मैं उपज खरीदता हूं'],
  fpoRole: ['I run a farmer group','मी शेतकरी गट चालवतो','मैं किसान समूह चलाता हूं'],
  farmerBenefit: ['List your harvest and compare buyer offers.','शेतमाल नोंदवा आणि खरेदीदारांच्या प्रस्तावांची तुलना करा.','अपनी उपज दर्ज करें और खरीदारों के प्रस्ताव देखें।'],
  buyerBenefit: ['Find available produce and send your own offer.','उपलब्ध शेतमाल शोधा आणि तुमचा प्रस्ताव पाठवा.','उपलब्ध उपज खोजें और अपना प्रस्ताव भेजें।'],
  fpoBenefit: ['Manage members and bring produce together.','सभासद आणि त्यांचा शेतमाल एकत्र व्यवस्थापित करा.','सदस्यों और उनकी उपज का एक साथ प्रबंधन करें।'],
  trustTitle: ['Clear information. Better decisions.','स्पष्ट माहिती. योग्य निर्णय.','स्पष्ट जानकारी। बेहतर फैसले।'],
  trustText: ['Market prices are a reference, not a guaranteed sale price. Agree quality, transport costs and payment terms with the buyer before accepting an offer.','बाजारभाव हा संदर्भ आहे, विक्रीची हमी नाही. प्रस्ताव स्वीकारण्यापूर्वी गुणवत्ता, वाहतूक खर्च आणि पैसे मिळण्याच्या अटी ठरवा.','बाजार भाव एक संदर्भ है, बिक्री की गारंटी नहीं। प्रस्ताव स्वीकार करने से पहले गुणवत्ता, परिवहन खर्च और भुगतान की शर्तें तय करें।'],
  help: ['Help','मदत','सहायता'],
  howItWorks: ['How it works','हे कसे चालते','यह कैसे काम करता है'],
  home: ['Home','मुख्यपृष्ठ','होम'],
  prices: ['Market prices','बाजारभाव','बाजार भाव'],
  map: ['Find markets','बाजार शोधा','बाजार खोजें'],
  login: ['Log in','लॉग इन करा','लॉग इन करें'],
  register: ['Create account','खाते तयार करा','खाता बनाएं'],
  logout: ['Log out','लॉग आउट','लॉग आउट'],
  dashboard: ['My overview','माझा आढावा','मेरा विवरण'],
  language: ['Language','भाषा','भाषा'],
  menu: ['Menu','मेनू','मेनू'],
  skip: ['Skip to content','मुख्य मजकुराकडे जा','मुख्य सामग्री पर जाएं'],
  crop: ['Crop','पीक','फसल'],
  district: ['District','जिल्हा','जिला'],
  state: ['State','राज्य','राज्य'],
  market: ['Market','बाजार','बाजार'],
  all: ['All','सर्व','सभी'],
  search: ['Search','शोधा','खोजें'],
  reportedPrice: ['Reported market price','नोंदवलेला बाजारभाव','दर्ज बाजार भाव'],
  referenceOnly: ['Reference price · final offers may differ','संदर्भ भाव · अंतिम किंमत वेगळी असू शकते','संदर्भ भाव · अंतिम कीमत अलग हो सकती है'],
  reportedOn: ['Reported','नोंद तारीख','दर्ज तारीख'],
  noDate: ['Date not provided','तारीख उपलब्ध नाही','तारीख उपलब्ध नहीं'],
  perQuintal: ['per quintal (100 kg)','प्रति क्विंटल (१०० किलो)','प्रति क्विंटल (१०० किलो)'],
  priceIntro: ['Compare prices with the market, date and unit in view.','बाजार, तारीख आणि एकक पाहून भावांची तुलना करा.','बाजार, तारीख और इकाई देखकर भावों की तुलना करें।'],
  rateEmpty: ['No prices reported for these filters. Try another crop or market.','या निवडीसाठी भाव उपलब्ध नाहीत. दुसरे पीक किंवा बाजार निवडा.','इस चयन के लिए भाव उपलब्ध नहीं हैं। दूसरी फसल या बाजार चुनें।'],
  empty: ['Nothing here yet','अजून नोंदी नाहीत','अभी कोई जानकारी नहीं'],
  loading: ['Loading…','माहिती येत आहे…','जानकारी आ रही है…'],
  retry: ['Try again','पुन्हा प्रयत्न करा','फिर कोशिश करें'],
  refresh: ['Refresh','नवीन माहिती पाहा','ताजा जानकारी देखें'],
  network: ['Cannot connect. Check your connection and try again.','जोडणी होत नाही. इंटरनेट तपासा आणि पुन्हा प्रयत्न करा.','कनेक्ट नहीं हो पा रहा। इंटरनेट जांचें और फिर कोशिश करें।'],
  timeout: ['This is taking longer than expected. Please try again.','अपेक्षेपेक्षा जास्त वेळ लागत आहे. पुन्हा प्रयत्न करा.','उम्मीद से ज्यादा समय लग रहा है। फिर कोशिश करें।'],
  server: ['We could not load this information. Please try again.','ही माहिती मिळाली नाही. पुन्हा प्रयत्न करा.','यह जानकारी नहीं मिली। फिर कोशिश करें।'],
  auth: ['Please check your login details or log in again.','लॉग इनची माहिती तपासा किंवा पुन्हा लॉग इन करा.','लॉगिन विवरण जांचें या फिर लॉग इन करें।'],
  forbidden: ['Your account cannot perform this action.','तुमच्या खात्याला ही कृती करता येत नाही.','आपके खाते से यह कार्रवाई नहीं हो सकती।'],
  conflict: ['This information has changed or already exists. Refresh and check before trying again.','ही माहिती बदलली आहे किंवा आधीपासून आहे. नवीन माहिती तपासा.','यह जानकारी बदल गई है या पहले से मौजूद है। फिर से जांचें।'],
  validation: ['Please check the details you entered.','भरलेली माहिती तपासा.','दर्ज जानकारी जांचें।'],
  rateLimited: ['Too many attempts. Wait a minute and try again.','खूप प्रयत्न झाले. एक मिनिट थांबून पुन्हा प्रयत्न करा.','बहुत कोशिशें हुईं। एक मिनट रुककर फिर प्रयास करें।'],
  offline: ['You are offline. You can keep a draft; submitting needs a connection.','इंटरनेट बंद आहे. मसुदा ठेवता येईल; पाठवण्यासाठी इंटरनेट लागेल.','आप ऑफलाइन हैं। मसौदा रख सकते हैं; भेजने के लिए इंटरनेट चाहिए।'],
  savedPrices: ['Saved prices · check the reported date','जतन केलेले भाव · नोंद तारीख तपासा','सहेजे हुए भाव · दर्ज तारीख जांचें'],
  name: ['Your name','तुमचे नाव','आपका नाम'],
  organization: ['Company or group name','कंपनी किंवा गटाचे नाव','कंपनी या समूह का नाम'],
  phone: ['Mobile number','मोबाइल क्रमांक','मोबाइल नंबर'],
  phoneHint: ['10-digit Indian mobile number; +91 is accepted.','१० अंकी भारतीय मोबाइल क्रमांक; +९१ चालेल.','10 अंकों का भारतीय मोबाइल नंबर; +91 स्वीकार है।'],
  email: ['Email (optional)','ईमेल (ऐच्छिक)','ईमेल (वैकल्पिक)'],
  identifier: ['Mobile number or email','मोबाइल क्रमांक किंवा ईमेल','मोबाइल नंबर या ईमेल'],
  password: ['Password','पासवर्ड','पासवर्ड'],
  passwordHint: ['Use at least 8 characters.','किमान ८ अक्षरे वापरा.','कम से कम 8 अक्षर रखें।'],
  showPassword: ['Show password','पासवर्ड दाखवा','पासवर्ड दिखाएं'],
  hidePassword: ['Hide password','पासवर्ड लपवा','पासवर्ड छिपाएं'],
  location: ['Village / collection location','गाव / शेतमाल उचलण्याचे ठिकाण','गांव / उपज उठाने का स्थान'],
  continue: ['Continue','पुढे जा','आगे बढ़ें'],
  back: ['Back','मागे','पीछे'],
  review: ['Review details','माहिती तपासा','जानकारी जांचें'],
  edit: ['Edit','बदला','बदलें'],
  cancel: ['Cancel','रद्द करा','रद्द करें'],
  loginTitle: ['Welcome back.','पुन्हा स्वागत.','फिर से स्वागत है।'],
  loginIntro: ['Log in to manage your crops, offers and orders.','शेतमाल, प्रस्ताव आणि व्यवहार पाहण्यासाठी लॉग इन करा.','फसल, प्रस्ताव और ऑर्डर देखने के लिए लॉग इन करें।'],
  intentNotice: ['Log in or create an account to continue. Your selection will be kept.','पुढे जाण्यासाठी लॉग इन करा किंवा खाते तयार करा. तुमची निवड जतन राहील.','आगे बढ़ने के लिए लॉग इन करें या खाता बनाएं। आपका चयन सुरक्षित रहेगा।'],
  newHere: ['New to KrishiLink?','KrishiLink वर नवीन आहात?','KrishiLink पर नए हैं?'],
  existing: ['Already have an account?','आधीपासून खाते आहे?','पहले से खाता है?'],
  registerTitle: ['Let’s get you started.','चला, सुरुवात करूया.','चलिए, शुरुआत करें।'],
  chooseRole: ['What brings you here?','तुम्हाला काय करायचे आहे?','आप क्या करना चाहते हैं?'],
  identityStep: ['About you','तुमची माहिती','आपके बारे में'],
  locationStep: ['Your location','तुमचे ठिकाण','आपका स्थान'],
  consent: ['I have read the Terms and Privacy information.','मी अटी आणि गोपनीयतेची माहिती वाचली आहे.','मैंने शर्तें और गोपनीयता की जानकारी पढ़ी है।'],
  terms: ['Terms','अटी','शर्तें'],
  privacy: ['Privacy','गोपनीयता','गोपनीयता'],
  quantity: ['Quantity','प्रमाण','मात्रा'],
  unit: ['Unit','एकक','इकाई'],
  quintal: ['Quintal','क्विंटल','क्विंटल'],
  kg: ['Kilogram','किलो','किलोग्राम'],
  tonne: ['Tonne','टन','टन'],
  askingPrice: ['Your asking price','तुमची अपेक्षित किंमत','आपकी मांगी कीमत'],
  grade: ['Quality grade (your estimate)','गुणवत्ता श्रेणी (तुमचा अंदाज)','गुणवत्ता श्रेणी (आपका अनुमान)'],
  grossTotal: ['Total before costs','खर्चापूर्वी एकूण रक्कम','खर्च से पहले कुल राशि'],
  costNote: ['Transport, quality checks and any other agreed costs are not included.','वाहतूक, गुणवत्ता तपासणी आणि इतर ठरलेले खर्च यात समाविष्ट नाहीत.','परिवहन, गुणवत्ता जांच और अन्य तय खर्च इसमें शामिल नहीं हैं।'],
  listingIntro: ['Tell buyers what is ready. You choose the asking price.','तयार शेतमालाची माहिती द्या. अपेक्षित किंमत तुम्ही ठरवा.','तैयार उपज की जानकारी दें। मांगी कीमत आप तय करें।'],
  prefilled: ['Filled from the price you viewed. Check and change anything before publishing.','तुम्ही पाहिलेल्या भावावरून माहिती भरली आहे. प्रसिद्ध करण्यापूर्वी तपासा.','आपके देखे भाव से जानकारी भरी है। प्रकाशित करने से पहले जांचें।'],
  publish: ['Publish listing','विक्रीची नोंद प्रसिद्ध करा','बिक्री की जानकारी प्रकाशित करें'],
  published: ['Your crop is listed.','तुमचा शेतमाल नोंदवला आहे.','आपकी फसल दर्ज हो गई।'],
  draftSaved: ['Draft saved on this device.','मसुदा या उपकरणावर जतन आहे.','मसौदा इस डिवाइस पर सुरक्षित है।'],
  listings: ['My listings','माझा शेतमाल','मेरी फसलें'],
  offers: ['Offers','प्रस्ताव','प्रस्ताव'],
  orders: ['Orders & payments','व्यवहार आणि पैसे','ऑर्डर और भुगतान'],
  findBuyers: ['Find buyers','खरेदीदार शोधा','खरीदार खोजें'],
  browse: ['Browse produce','शेतमाल पाहा','उपज देखें'],
  makeOffer: ['Make an offer','प्रस्ताव द्या','प्रस्ताव दें'],
  sendOffer: ['Send offer','प्रस्ताव पाठवा','प्रस्ताव भेजें'],
  offerPrice: ['Your offer per unit','प्रति एकक तुमची किंमत','प्रति इकाई आपकी कीमत'],
  offerSent: ['Offer sent. Track it in Offers.','प्रस्ताव पाठवला. प्रस्ताव विभागात पाहा.','प्रस्ताव भेजा गया। प्रस्ताव विभाग में देखें।'],
  offerReview: ['Review this offer before confirming.','खात्री करण्यापूर्वी प्रस्ताव तपासा.','पुष्टि करने से पहले प्रस्ताव जांचें।'],
  accept: ['Accept offer','प्रस्ताव स्वीकारा','प्रस्ताव स्वीकारें'],
  reject: ['Decline','नाकारा','अस्वीकार करें'],
  confirm: ['Confirm','खात्री करा','पुष्टि करें'],
  accepted: ['Offer accepted. View your order for next steps.','प्रस्ताव स्वीकारला. पुढील माहितीसाठी व्यवहार पाहा.','प्रस्ताव स्वीकारा गया। आगे के लिए ऑर्डर देखें।'],
  declined: ['Offer declined.','प्रस्ताव नाकारला.','प्रस्ताव अस्वीकार किया गया।'],
  pending: ['Pending','प्रलंबित','लंबित'],
  noOffers: ['Offers will appear here when a buyer responds to a listing.','खरेदीदाराने प्रतिसाद दिल्यावर प्रस्ताव येथे दिसतील.','खरीदार के जवाब देने पर प्रस्ताव यहां दिखेंगे।'],
  noListings: ['Start with your first crop listing.','तुमच्या पहिल्या शेतमालाची नोंद करा.','अपनी पहली फसल दर्ज करें।'],
  noOrders: ['Accepted offers create orders here.','स्वीकारलेल्या प्रस्तावांचे व्यवहार येथे दिसतील.','स्वीकृत प्रस्तावों के ऑर्डर यहां दिखेंगे।'],
  paymentNote: ['An order status is not a bank receipt. Confirm money received in your bank account.','व्यवहाराची स्थिती म्हणजे बँकेची पावती नाही. खात्यात पैसे आल्याची खात्री करा.','ऑर्डर की स्थिति बैंक रसीद नहीं है। अपने खाते में पैसे आने की पुष्टि करें।'],
  status: ['Status','स्थिती','स्थिति'],
  helpTitle: ['A little help, at every step.','प्रत्येक पायरीवर थोडी मदत.','हर कदम पर थोड़ी मदद।'],
  helpIntro: ['Choose the task you need help with.','ज्या कामासाठी मदत हवी ते निवडा.','जिस काम में सहायता चाहिए उसे चुनें।'],
  raiseIssue: ['Report a problem','समस्या नोंदवा','समस्या बताएं'],
  support: ['My support requests','माझ्या मदतीच्या विनंत्या','मेरे सहायता अनुरोध'],
  subject: ['What happened?','काय झाले?','क्या हुआ?'],
  description: ['Tell us more','अधिक माहिती द्या','अधिक बताएं'],
  submit: ['Submit request','विनंती पाठवा','अनुरोध भेजें'],
  submitted: ['Your request was saved. You can follow its status here.','तुमची विनंती जतन झाली. तिची स्थिती येथे पाहा.','आपका अनुरोध सुरक्षित है। उसकी स्थिति यहां देखें।'],
  notFound: ['We couldn’t find that page.','हे पृष्ठ सापडले नाही.','यह पेज नहीं मिला।'],
  returnHome: ['Back to home','मुख्यपृष्ठावर जा','होम पर जाएं'],
  about: ['About KrishiLink','KrishiLink बद्दल','KrishiLink के बारे में'],
  aboutText: ['KrishiLink helps farmers, buyers and farmer groups discover prices and organise produce trading. Availability depends on listed produce and participating buyers.','KrishiLink शेतकरी, खरेदीदार आणि शेतकरी गटांना भाव पाहण्यास व शेतमाल व्यापार व्यवस्थापित करण्यास मदत करते. उपलब्धता नोंदवलेल्या शेतमालावर आणि खरेदीदारांवर अवलंबून असते.','KrishiLink किसानों, खरीदारों और किसान समूहों को भाव देखने और उपज व्यापार व्यवस्थित करने में मदद करता है। उपलब्धता दर्ज उपज और खरीदारों पर निर्भर है।'],
  footerText: ['Closer to your market. Clearer about your choices.','बाजाराच्या जवळ. निर्णयासाठी स्पष्ट माहिती.','बाजार के करीब। फैसलों के लिए स्पष्ट जानकारी।'],
  members: ['Members','सभासद','सदस्य'],
  addMember: ['Add member','सभासद जोडा','सदस्य जोड़ें'],
  groupLots: ['Group listings','गटाचा शेतमाल','समूह की उपज'],
  groupTitle: ['Your farmer group','तुमचा शेतकरी गट','आपका किसान समूह'],
  combine: ['Combine selected produce','निवडलेला शेतमाल एकत्र करा','चुनी उपज एक साथ करें'],
  readyQty: ['Ready quantity (quintals)','तयार प्रमाण (क्विंटल)','तैयार मात्रा (क्विंटल)'],
  notes: ['Note (optional)','टीप (ऐच्छिक)','टिप्पणी (वैकल्पिक)'],
  previous: ['Previous','मागील','पिछला'],
  next: ['Next','पुढील','अगला'],
};
export const copy = Object.fromEntries(['en','mr','hi'].map((locale,index) => [locale, Object.fromEntries(Object.entries(rows).map(([key,values]) => [key,values[index]]))]));


const additional = {
  "sameCropGrade": [
    "Select members with the same crop and grade.",
    "एकाच पिकाचे आणि श्रेणीचे सभासद निवडा.",
    "एक ही फसल और श्रेणी के सदस्य चुनें।"
  ],
  "accountHelp": [
    "Help with your account",
    "खात्यासाठी मदत",
    "खाते में सहायता"
  ],
  "accountHelpText": [
    "Use the mobile number or email you registered with and your password. Spaces and the +91 prefix are accepted in mobile numbers. Password recovery delivery is not configured in this installation.",
    "नोंदणी केलेला मोबाइल क्रमांक किंवा ईमेल आणि पासवर्ड वापरा. मोबाइल क्रमांकात मोकळी जागा आणि +९१ चालते. या आवृत्तीत पासवर्ड पुनर्प्राप्ती सेवा जोडलेली नाही.",
    "पंजीकृत मोबाइल नंबर या ईमेल और पासवर्ड इस्तेमाल करें। नंबर में खाली जगह और +91 स्वीकार हैं। इस संस्करण में पासवर्ड पुनर्प्राप्ति सेवा जुड़ी नहीं है।"
  ],
  "supportAvailability": [
    "Signed-in users can save and track support requests. Phone support hours and response times have not been published.",
    "लॉग इन केलेले वापरकर्ते मदतीची विनंती नोंदवू आणि पाहू शकतात. फोन मदतीची वेळ आणि उत्तराची मुदत प्रकाशित केलेली नाही.",
    "लॉग इन उपयोगकर्ता सहायता अनुरोध दर्ज और देख सकते हैं। फोन सहायता के समय और उत्तर की अवधि प्रकाशित नहीं हैं।"
  ],
  "policyStatus": [
    "This installation is a development preview. Operator details, final fees and reviewed legal policies must be published before public trading.",
    "ही आवृत्ती विकासातील पूर्वदृश्य आहे. सार्वजनिक व्यापारापूर्वी संचालकांची माहिती, अंतिम शुल्क आणि तपासलेल्या कायदेशीर अटी प्रकाशित करणे आवश्यक आहे.",
    "यह संस्करण विकास पूर्वावलोकन है। सार्वजनिक व्यापार से पहले संचालक विवरण, अंतिम शुल्क और समीक्षित कानूनी नीतियां प्रकाशित होनी चाहिए।"
  ],
  "dataCollected": [
    "Information stored",
    "जतन केलेली माहिती",
    "संग्रहित जानकारी"
  ],
  "dataCollectedText": [
    "Accounts store your name, mobile number, optional email, role and location. Listings, offers and support requests store the details you submit. Passwords are hashed on the server.",
    "खात्यात नाव, मोबाइल क्रमांक, ऐच्छिक ईमेल, भूमिका आणि ठिकाण जतन होते. शेतमाल, प्रस्ताव आणि मदतीच्या विनंत्यांमध्ये तुम्ही दिलेली माहिती जतन होते. पासवर्ड सर्व्हरवर सुरक्षित स्वरूपात ठेवले जातात.",
    "खाते में नाम, मोबाइल नंबर, वैकल्पिक ईमेल, भूमिका और स्थान सुरक्षित होते हैं। उपज, प्रस्ताव और सहायता अनुरोध में आपकी दी जानकारी रहती है। पासवर्ड सर्वर पर सुरक्षित रूप में रखे जाते हैं।"
  ],
  "dataUse": [
    "How information is used",
    "माहितीचा वापर",
    "जानकारी का उपयोग"
  ],
  "dataUseText": [
    "Listing details are visible to buyers. Account and trade details support matching, offers, orders and issue resolution. Avoid putting sensitive personal details in public listing text.",
    "शेतमालाची माहिती खरेदीदारांना दिसते. खाते आणि व्यवहारांची माहिती प्रस्ताव, व्यवहार आणि समस्यांसाठी वापरली जाते. सार्वजनिक नोंदीत संवेदनशील वैयक्तिक माहिती टाकू नका.",
    "उपज विवरण खरीदारों को दिखते हैं। खाता और व्यापार विवरण प्रस्ताव, ऑर्डर और समस्याओं के लिए इस्तेमाल होते हैं। सार्वजनिक विवरण में संवेदनशील निजी जानकारी न डालें।"
  ],
  "deviceStorage": [
    "On this device",
    "या उपकरणावर",
    "इस डिवाइस पर"
  ],
  "deviceStorageText": [
    "Language choice, listing drafts and sign-in information are stored in this browser. Registration drafts exclude passwords. Log out when using a shared device.",
    "भाषेची निवड, शेतमालाचे मसुदे आणि लॉग इनची माहिती या ब्राउझरमध्ये जतन होते. नोंदणीच्या मसुद्यात पासवर्ड नसतो. सामायिक उपकरणावरून लॉग आउट करा.",
    "भाषा, उपज मसौदे और लॉगिन जानकारी इस ब्राउज़र में रहती है। पंजीकरण मसौदे में पासवर्ड नहीं रहता। साझा डिवाइस पर लॉग आउट करें।"
  ],
  "privacyContact": [
    "Questions about your data",
    "तुमच्या माहितीबद्दल प्रश्न",
    "आपके डेटा के बारे में प्रश्न"
  ],
  "privacyContactText": [
    "Use a support request to raise a data question. Published operator contact details, retention periods and an operational deletion process are still required before a public release.",
    "माहितीबद्दल प्रश्नासाठी मदतीची विनंती करा. सार्वजनिक प्रकाशनापूर्वी संचालकांचा संपर्क, माहिती ठेवण्याचा कालावधी आणि हटवण्याची प्रक्रिया आवश्यक आहे.",
    "डेटा के प्रश्न के लिए सहायता अनुरोध करें। सार्वजनिक रिलीज से पहले संचालक संपर्क, डेटा रखने की अवधि और हटाने की प्रक्रिया आवश्यक है।"
  ],
  "tradeTerms": [
    "Before agreeing to a trade",
    "व्यवहार ठरवण्यापूर्वी",
    "व्यापार तय करने से पहले"
  ],
  "tradeTermsText": [
    "Check the crop, quality, quantity, location and price. Only send or accept an offer after checking its total. Listing a crop does not guarantee a buyer.",
    "पीक, गुणवत्ता, प्रमाण, ठिकाण आणि किंमत तपासा. एकूण रक्कम तपासूनच प्रस्ताव पाठवा किंवा स्वीकारा. नोंद केल्याने खरेदीदार मिळण्याची हमी नाही.",
    "फसल, गुणवत्ता, मात्रा, स्थान और कीमत जांचें। कुल राशि जांचकर ही प्रस्ताव भेजें या स्वीकारें। उपज दर्ज करने से खरीदार की गारंटी नहीं है।"
  ],
  "priceTerms": [
    "Market price information",
    "बाजारभावाची माहिती",
    "बाजार भाव की जानकारी"
  ],
  "priceTermsText": [
    "Reported prices refer to a specific market and date. They are not guaranteed offers. Compare like units and account for transport and other agreed costs.",
    "नोंदवलेले भाव ठराविक बाजार आणि तारखेचे असतात. ते हमीचे प्रस्ताव नाहीत. समान एककात तुलना करा आणि वाहतूक व इतर खर्च विचारात घ्या.",
    "दर्ज भाव किसी बाजार और तारीख के होते हैं। वे गारंटीकृत प्रस्ताव नहीं हैं। समान इकाई में तुलना करें और परिवहन व अन्य खर्च देखें।"
  ],
  "paymentTerms": [
    "Payments and costs",
    "पैसे आणि खर्च",
    "भुगतान और खर्च"
  ],
  "paymentTermsText": [
    "The interface records orders; this preview does not move bank funds. No guaranteed settlement time or fee-free trade is promised. Agree costs and payment arrangements before proceeding.",
    "हे पूर्वदृश्य व्यवहार नोंदवते; बँकेतील पैसे पाठवत नाही. ठराविक वेळेत पैसे मिळण्याची किंवा विनाशुल्क व्यापाराची हमी नाही. पुढे जाण्यापूर्वी खर्च आणि पैसे मिळण्याची पद्धत ठरवा.",
    "यह पूर्वावलोकन ऑर्डर दर्ज करता है; बैंक पैसे नहीं भेजता। निश्चित समय पर भुगतान या मुफ्त व्यापार का वादा नहीं है। आगे बढ़ने से पहले खर्च और भुगतान तय करें।"
  ],
  "status_PENDING": [
    "Pending",
    "प्रलंबित",
    "लंबित"
  ],
  "status_PUBLISHED": [
    "Listed",
    "नोंदवलेले",
    "दर्ज"
  ],
  "status_ACCEPTED": [
    "Accepted",
    "स्वीकारले",
    "स्वीकृत"
  ],
  "status_REJECTED": [
    "Declined",
    "नाकारले",
    "अस्वीकृत"
  ],
  "status_CREATED": [
    "Order created",
    "व्यवहार तयार",
    "ऑर्डर बना"
  ],
  "status_PAYMENT_PENDING": [
    "Payment pending",
    "पैसे प्रलंबित",
    "भुगतान लंबित"
  ],
  "status_PAYMENT_CONFIRMED": [
    "Payment recorded",
    "पैसे नोंदवले",
    "भुगतान दर्ज"
  ],
  "status_PROCESSING": [
    "Preparing produce",
    "शेतमाल तयारी",
    "उपज तैयार हो रही"
  ],
  "status_READY_FOR_DISPATCH": [
    "Ready for pickup",
    "उचलण्यासाठी तयार",
    "उठाने के लिए तैयार"
  ],
  "status_IN_TRANSIT": [
    "On the way",
    "वाटेत",
    "रास्ते में"
  ],
  "status_DELIVERED": [
    "Delivered",
    "पोहोचले",
    "पहुंचाया"
  ],
  "status_COMPLETED": [
    "Completed",
    "पूर्ण",
    "पूरा"
  ],
  "status_CANCELLED": [
    "Cancelled",
    "रद्द",
    "रद्द"
  ],
  "status_DISPUTED": [
    "Issue reported",
    "समस्या नोंदवली",
    "समस्या दर्ज"
  ],
  "status_OPEN": [
    "Open",
    "नोंदवले",
    "दर्ज"
  ],
  "status_RESOLVED": [
    "Resolved",
    "सोडवले",
    "हल"
  ],
  "status_CLOSED": [
    "Closed",
    "बंद",
    "बंद"
  ],
  "status_UNDER_REVIEW": [
    "Under review",
    "तपासणी सुरू",
    "जांच जारी"
  ]
};
for (const [key, values] of Object.entries(additional)) ['en','mr','hi'].forEach((locale,i)=>{copy[locale][key]=values[i];});
