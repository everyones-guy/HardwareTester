-- Synthetic launch page. The maintenance mode handler has no reviewed binding.
INSERT INTO "PagesInstalled" ("PageName", "PageID", "PageConfig") VALUES
  ('Maintenance', 20, '{"Resources":{"resource":[{"tag":"Title","value":"Maintenance"}]}}');
INSERT INTO "WidgetsInstalled" ("WidgetConfigID", "WidgetID", "WidgetConfig") VALUES
  (2001, 201, '{"Resources":{"resource":[{"tag":"Name","value":"MaintenanceMode"},{"tag":"ButtonType","value":"Button"},{"tag":"WidgetIndex","value":"1"},{"tag":"Handler","value":"confirmMaintenanceMode"}]}}'),
  (2002, 202, '{"Resources":{"resource":[{"tag":"Name","value":"Open Valve Station"},{"tag":"ButtonType","value":"Navigate"},{"tag":"TargetPageID","value":10}]}}');
