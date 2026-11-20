-- Synthetic controller sample in the UISee PagesInstalled / WidgetsInstalled format.
INSERT INTO "PagesInstalled" ("PageName", "PageID", "PageConfig") VALUES
  ('Valve Station', 10, '{"Resources":{"resource":[{"tag":"Title","value":"Valve Station"}]}}');
INSERT INTO "WidgetsInstalled" ("WidgetConfigID", "WidgetID", "WidgetConfig") VALUES
  (1001, 101, '{"Resources":{"resource":[{"tag":"Name","value":"ValveTarget"},{"tag":"ButtonType","value":"Numeric"},{"tag":"WidgetIndex","value":"1"},{"tag":"MinValue","value":0},{"tag":"MaxValue","value":100},{"tag":"Step","value":1},{"tag":"Handler","value":"setValveTarget"}]}}');
