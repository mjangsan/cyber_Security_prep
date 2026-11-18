# Lab Write-up: Exploiting a Mass Assignment Vulnerability

## Objective

Buy the jacket without spending any money (i.e., without enough store credit).

## Background: Mass Assignment

Mass assignment (also called **auto-binding**) happens when a framework automatically binds the parameters of a request to fields of an internal object or model. If the application doesn't restrict which fields can be bound, an attacker can add **hidden or unintended parameters** to the request JSON body and modify fields the developer never meant to expose, such as price, role, or discount.

## Initial Setup

1. Log in with the credentials provided by the lab.
2. Add the jacket to the cart.
3. Try to place the order with the current store credit. The purchase fails because the credit is not enough to cover the price of the jacket.

## Analysis

To buy the jacket without paying, there are only two options:

1. Increase the store credit, or
2. Reduce the price of the jacket to 0.

### Attempt 1: Increase the store credit (failed)

I looked for a way to raise the store credit but found no endpoint in the captured requests that modifies it, and no client-side scripts referencing it. This path was a dead end.

### Attempt 2: Reduce the price / apply a discount (successful)

While adding the item to the cart, I noticed that an additional request was being sent:

```
/api/checkout
```

This endpoint is called with both `GET` and `POST`, and the response body contains JSON data. This is a good place to look for hidden parameters.

## Exploitation Steps

1. In **Proxy > HTTP history**, notice both the `GET` and `POST` API requests for `/api/checkout`.
2. Notice that the response to the `GET` request contains the same JSON structure as the `POST` request. Observe that the JSON structure in the `GET` response includes a `chosen_discount` parameter, which is **not present** in the `POST` request.
3. Right-click the `POST /api/checkout` request and select **Send to Repeater**.
4. In Repeater, add the `chosen_discount` parameter to the request. The JSON should look like the following:

   ```json
   {
       "chosen_discount": {
           "percentage": 0
       },
       "chosen_products": [
           {
               "product_id": "1",
               "quantity": 1
           }
       ]
   }
   ```

5. Send the request. Notice that adding the `chosen_discount` parameter doesn't cause an error.
6. Change the `chosen_discount` value to the string `"x"`, then send the request. Observe that this results in an error message as the parameter value isn't a number. This may indicate that the user input is being processed (i.e., the parameter is bound server-side).
7. Change the `chosen_discount` percentage to `100`, then send the request to solve the lab:

   ```json
   {
       "chosen_discount": {
           "percentage": 100
       },
       "chosen_products": [
           {
               "product_id": "1",
               "quantity": 1
           }
       ]
   }
   ```

## Result

The jacket was purchased with a 100% discount, so no store credit was spent. The lab is solved.

## Root Cause

The `POST /api/checkout` endpoint automatically binds every field in the JSON body to the internal order object. The `chosen_discount` field was intended to be set only by the server (it appears in the `GET` response), but because the server doesn't restrict which fields the client can supply, the user can set it directly.

## Remediation

- Use an **allow-list** of properties that can be bound from user input (e.g., DTOs or explicit field mapping).
- Mark sensitive fields (price, discount, role, balance) as read-only or non-bindable.
- Never trust client-supplied values for pricing or discounts; compute them server-side.
- Validate the type and range of all accepted values.

## Key Takeaways

- Compare `GET` responses with `POST` request bodies to spot parameters that exist on the server object but are not sent by the client.
- Send an invalid value (like `"x"`) to confirm whether a hidden parameter is actually processed.
- Always test hidden parameters with extreme values after confirming they're accepted.
