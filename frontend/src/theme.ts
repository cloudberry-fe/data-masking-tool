import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context'

// Apache Style Theme - Cloudberry Blue
export const themeConfig: ThemeConfig = {
  token: {
    colorPrimary: '#2563eb',
    colorPrimaryHover: '#3b82f6',
    colorPrimaryActive: '#1d4ed8',
    colorLink: '#2563eb',
    colorLinkHover: '#3b82f6',
    colorSuccess: '#16a34a',
    colorWarning: '#f97316',
    colorError: '#dc2626',
    colorInfo: '#0ea5e9',
    colorText: '#1e293b',
    colorTextSecondary: '#64748b',
    colorBorder: '#e2e8f0',
    colorBgContainer: '#ffffff',
    colorBgLayout: '#f8fafc',
    borderRadius: 6,
    fontSize: 14,
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif",
  },
  components: {
    Button: {
      borderRadius: 6,
      controlHeight: 36,
    },
    Input: {
      borderRadius: 6,
      controlHeight: 36,
    },
    Select: {
      borderRadius: 6,
      controlHeight: 36,
    },
    Table: {
      borderRadius: 6,
      headerBg: '#f8fafc',
    },
    Menu: {
      itemSelectedBg: 'rgba(37, 99, 235, 0.08)',
      itemSelectedColor: '#2563eb',
      itemHoverColor: '#2563eb',
      itemBg: '#ffffff',
    },
    Card: {
      borderRadius: 8,
      headerBg: '#ffffff',
    },
    Tabs: {
      horizontalItemPadding: '16px 0',
      itemSelectedColor: '#2563eb',
      itemHoverColor: '#2563eb',
      inkBarColor: '#2563eb',
    },
  },
}
