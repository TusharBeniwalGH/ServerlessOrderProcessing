using Amazon.Lambda.Core;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.DocumentModel;
using System.Text.Json;
// Assembly attribute to enable the Lambda function's JSON input to be converted into a .NET class.
[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace OrderSubmission
{
    public class OrderHandler
    {
        protected readonly string _tableName;
        protected readonly AmazonDynamoDBClient amazonDynamoDBClient;
        public OrderHandler()
        {
            _tableName = Environment.GetEnvironmentVariable("ORDERS_TABLE")
                        ?? throw new Exception("ORDERS_TABLE environment variable is not set.");
            amazonDynamoDBClient = new AmazonDynamoDBClient();
        }
        public async Task<APIGatewayProxyResponse> SubmitOrder(APIGatewayProxyRequest request, ILambdaContext context)
        {
            try
            {
                var order = JsonSerializer.Deserialize<Order>(request.Body);
                var table = new TableBuilder(amazonDynamoDBClient, _tableName).AddHashKey("OrderId", DynamoDBEntryType.String).Build();

                var doc = new Document
                {
                    ["OrderId"] = Guid.NewGuid().ToString(),
                    ["CustomerName"] = order?.CustomerName,
                    ["Items"] = JsonSerializer.Serialize(order?.Items),
                    ["Status"] = "Pending",
                    ["OrderDate"] = DateTime.UtcNow.ToString("o")

                };
                await table.PutItemAsync(doc);
                return new APIGatewayProxyResponse
                {
                    StatusCode = 200,
                    Body = "Order submitted successfully"
                };

            }
            catch (Exception ex)
            {
                return new APIGatewayProxyResponse
                {
                    StatusCode = 500,
                    Body = $"Error:{ex.Message}"
                };
            }
        }

        public class Order
        {
            public string? CustomerName { get; set; }
            public List<string>? Items { get; set; }
        }
    }
}
