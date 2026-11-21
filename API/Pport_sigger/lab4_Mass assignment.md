# Lab 4 – Exploiting a Mass Assignment Vulnerability

**Platform:** PortSwigger Web Security Academy (API testing)
**Category:** Mass assignment / auto-binding
**Goal:** Buy the *Lightweight "l33t" Leather Jacket* without spending any money.

## Background
Mass assignment (also called *auto-binding*) happens when a framework automatically maps the fields of a request body onto an internal object. If the developer doesn't restrict which fields are allowed, a client can supply **hidden parameters** that were never meant to be user-controlled (price, role, discount, etc.).

## Approach

### 1. Set up
- Logged in with the credentials provided by the lab.
- Added the jacket to the cart.
- Tried to place the order: it failed because my store credit was too low.

### 2. Thinking about the options
To buy the jacket for free I need to either:
1. increase my store credit, or
2. reduce the price of the jacket to 0.

### 3. Option 1 – raising store credit (dead end)
I looked for a request or script that changes the account balance and found no endpoint or client-side code for it, so I dropped this idea.

### 4. Option 2 – look for hidden parameters
While adding the item to the cart, I noticed an extra API call in **Proxy > HTTP history**:

```
GET  /api/checkout
POST /api/checkout
```

Comparing the two:

- The `GET` response contains a JSON body that includes a **`chosen_discount`** object.
- The `POST` request (what the app actually sends) does **not** include `chosen_discount`.

That difference suggests the server model has a `chosen_discount` field that the client never sets, so it may be bindable.

![GET vs POST /api/checkout and the chosen_discount parameter](./screenshots/01-checkout-chosen-discount.png)

### 5. Testing the hidden parameter
Sent `POST /api/checkout` to **Repeater** and added the parameter:

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

- The request was accepted without an error, so the server does read the field.
- Changing `percentage` to the string `"x"` returned an error complaining that the value is not a number. This confirms the server **processes** my input and binds it to the object.

### 6. Exploit
Set the discount to 100%:

```json
"chosen_discount": { "percentage": 100 }
```

Sending the request completed the order for a total of $0, which solved the lab.

## Root cause
The checkout endpoint binds the whole request body to an internal order object without a whitelist, so a client can set the `chosen_discount` field that should be server-controlled.

## Remediation
- Allow-list the fields a client may submit (use DTOs / explicit binding instead of auto-binding).
- Never accept price, discount or role data from the client; compute them server-side.
- Reject unexpected fields in request bodies.

## Takeaways
- Compare `GET` and `POST` responses on the same endpoint: fields that appear in one and not the other are candidates for hidden parameters.
- Use invalid values (like a string where a number is expected) to confirm a parameter is actually being processed.