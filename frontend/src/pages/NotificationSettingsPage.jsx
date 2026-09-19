import WebPushPreferences from '../components/WebPushPreferences';
import { PageHeading } from '../components/Experience';
import { useLanguage } from '../hooks/useLanguage';

export default function NotificationSettingsPage() {
  const { t } = useLanguage();
  return (
    <div className="notification-settings-page">
      <PageHeading title={t('notificationSettings')} description={t('pushPrivacyNote')} />
      <WebPushPreferences />
    </div>
  );
}
