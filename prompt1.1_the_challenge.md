This challenge is to build your own URL shortening service. Think bit.ly or
tinyurl.com.

Basically it’s a service that lets a client submit a long URL which is then
shortened to make it easier to use. For example:

https://www.amazon.com/Rust-Programming-Language-2nd/dp/1718503105/ref=sr_1_1?crid=3977W67XGQPJR&keywords=the+rust+programming+language&qid=1685542718&sprefix=the+%2Caps%2C3079&sr=8-1

could become: https://tinyurl.com/bdds8utd

This is typically done with a web based user interface, that let’s users enter a
long URL and get back a shortened version of the URL. For example:

The shortening service then keeps a record of the short code, i.e. bdds8utd in
the example above and the long URL that it maps to. Then when a client requests
the shortened URL the service returns a HTTP redirect code, sending them to the
long URL.