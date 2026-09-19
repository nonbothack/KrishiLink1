import { describe, expect, it } from 'vitest';
import { copy } from './copy';

describe('public product copy', () => {
  it('has reviewed English, Marathi and Hindi strings for every public key', () => {
    const publicKeys = Object.keys(copy.en).filter((key) => key.startsWith('public'));
    expect(publicKeys.length).toBeGreaterThan(0);
    for (const key of publicKeys) {
      for (const locale of ['en', 'mr', 'hi']) {
        expect(typeof copy[locale][key], `${locale}.${key}`).toBe('string');
        expect(copy[locale][key].trim(), `${locale}.${key}`).not.toBe('');
      }
    }
  });
});

describe('Trade Room copy', () => {
  it('has English, Marathi and Hindi text for operations and provenance states', () => {
    const keys = [
      'tradeRoom', 'tradeRoomIntro', 'tradeReference', 'agreedGross', 'agreedTerms', 'deliveryTerms',
      'paymentNoMovement', 'tradeTimeline', 'tradeNote', 'tradeNoteSaved', 'noTradeEvents', 'needHelp',
      'tradeSupportHelp', 'tradeLinkedIssue', 'tradeUnavailable', 'addTradeNote', 'noteDetails', 'saveNote',
      'termsUnavailable', 'paymentReport', 'paymentReportIntro', 'paymentReference', 'reportedAmount',
      'reportPaymentSent', 'acknowledgeReport', 'acknowledgeWarning', 'participantReported',
      'providerNotConnected', 'qualitySection', 'qualityIntro', 'qualityClaim', 'recordStatement',
      'weighmentSection', 'weighmentIntro', 'grossQuantity', 'tareQuantity', 'recordWeighment',
      'logisticsSection', 'logisticsIntro', 'pickupReported', 'dispatchReported', 'deliveryReported',
      'receiptConfirmed', 'recordLogistics', 'storageSection', 'storageRequestIntro', 'chooseFacility',
      'requestStorage', 'pendingFacility', 'noFacilities', 'storageDemo', 'evidenceSection', 'evidenceIntro',
      'uploadEvidence', 'evidenceType', 'qualityPhoto', 'weighmentDocument', 'deliveryDocument', 'otherEvidence',
      'participantSubmitted', 'sellerAcknowledged', 'notAcknowledged', 'noAssay', 'netQuantity', 'difference',
      'operationSaved', 'chooseAction', 'optionalDetails', 'bytes', 'viewEvidence', 'operatorRecorded',
      'platformRecorded', 'timelinePaymentReported', 'timelinePaymentAcknowledged', 'timelineQualityClaim',
      'timelineQualityObservation', 'timelineWeighment', 'timelinePickup', 'timelineDispatch', 'timelineDelivery',
      'timelineReceipt', 'timelineStorageRequest', 'timelineEvidence', 'timelineDisputeOpened', 'timelineDisputeUpdated',
      'legacyPaymentRecord', 'legacyPaymentWarning',
    ];
    for (const key of keys) {
      for (const locale of ['en', 'mr', 'hi']) {
        expect(typeof copy[locale][key], `${locale}.${key}`).toBe('string');
        expect(copy[locale][key].trim(), `${locale}.${key}`).not.toBe('');
      }
  }
});

describe('Packet 12 offline and reach copy', () => {
  it('has non-empty English, Hindi and Marathi strings for every offline/simple-mode/voice/update key', () => {
    const keys = Object.keys(copy.en).filter((key) =>
      /^(offline|simpleMode|voice|dictate|readAloud|stopReading|appUpdate|updateAfterForm)/i.test(key),
    );
    expect(keys.length).toBeGreaterThan(10);
    for (const key of keys) {
      for (const locale of ['en', 'hi', 'mr']) {
        expect(typeof copy[locale][key], `${locale}.${key}`).toBe('string');
        expect(copy[locale][key].trim(), `${locale}.${key}`).not.toBe('');
      }
    }
  });
});
});
