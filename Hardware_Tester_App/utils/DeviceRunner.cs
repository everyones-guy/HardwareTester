using System;
using System.IO;
using System.Reflection;
using Newtonsoft.Json.Linq;

class DeviceRunner
{
    public static void Main(string[] args)
    {
        string jsonPath = args.Length > 0 ? args[0] : "device.json";

        if (!File.Exists(jsonPath))
        {
            Console.WriteLine($"JSON file not found: {jsonPath}");
            return;
        }

        try
        {
            // Read and parse JSON
            var jsonData = JObject.Parse(File.ReadAllText(jsonPath));

            string dllPath = jsonData["metadata"]?["dll_path"]?.ToString();
            string entryPoint = jsonData["metadata"]?["entry_point"]?.ToString();
            string method = jsonData["metadata"]?["method"]?.ToString();
            JArray parameters = (JArray)jsonData["metadata"]?["parameters"];

            if (string.IsNullOrEmpty(dllPath) || string.IsNullOrEmpty(entryPoint) || string.IsNullOrEmpty(method))
            {
                Console.WriteLine("Invalid metadata in JSON. Ensure 'dll_path', 'entry_point', and 'method' are specified.");
                return;
            }

            // Load the DLL
            var assembly = Assembly.LoadFrom(dllPath);

            // Get the target class and method
            var targetType = assembly.GetType(entryPoint);
            if (targetType == null)
            {
                Console.WriteLine($"Class '{entryPoint}' not found in {dllPath}");
                return;
            }

            var targetMethod = targetType.GetMethod(method);
            if (targetMethod == null)
            {
                Console.WriteLine($"Method '{method}' not found in class '{entryPoint}'");
                return;
            }

            // Create an instance of the target class
            var targetInstance = Activator.CreateInstance(targetType);

            // Convert JSON parameters to an object array
            object[] methodParameters = parameters?.ToObject<object[]>() ?? new object[] { };

            // Invoke the method with parameters
            var result = targetMethod.Invoke(targetInstance, methodParameters);

            Console.WriteLine($"Method '{method}' executed successfully. Result: {result}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error executing device: {ex.Message}");
        }
    }
}
