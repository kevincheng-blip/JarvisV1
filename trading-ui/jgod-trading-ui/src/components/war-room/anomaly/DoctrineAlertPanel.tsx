/**
 * DoctrineAlertPanel Component
 * 
 * Anomaly Layer - Doctrine Alert Panel
 * 
 * 顯示 Doctrine 紅線警示
 */

export function DoctrineAlertPanel() {
  // Placeholder data structure
  // In future, this should come from DoctrineAlert API
  const alerts = [
    { id: '1', level: 'HIGH', message: '單筆曝險超過 10% 上限', doctrine: 'book_05', timestamp: new Date().toISOString() },
    { id: '2', level: 'MEDIUM', message: '連續 3 日虧損，建議減倉', doctrine: 'book_07', timestamp: new Date().toISOString() },
  ];

  const getAlertColor = (level: string) => {
    switch (level) {
      case 'HIGH':
        return 'border-red-500 bg-red-50 dark:bg-red-900/20';
      case 'MEDIUM':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      case 'LOW':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-900/20';
      default:
        return 'border-gray-500 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Doctrine 紅線警示
      </h3>
      {alerts.length === 0 ? (
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          目前沒有警示
        </div>
      ) : (
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3 rounded-lg border-l-4 ${getAlertColor(alert.level)}`}
            >
              <div className="flex justify-between items-start mb-1">
                <span
                  className={`text-xs font-semibold px-2 py-1 rounded ${
                    alert.level === 'HIGH'
                      ? 'bg-red-500 text-white'
                      : alert.level === 'MEDIUM'
                      ? 'bg-yellow-500 text-white'
                      : 'bg-blue-500 text-white'
                  }`}
                >
                  {alert.level}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-500">
                  {alert.doctrine}
                </span>
              </div>
              <div className="text-sm text-gray-900 dark:text-white">
                {alert.message}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                {new Date(alert.timestamp).toLocaleString('zh-TW')}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

