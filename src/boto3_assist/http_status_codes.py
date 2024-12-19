"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

from enum import Enum


class HttpStatusCodes(Enum):
    """Http Status Codes"""

    HTTP_400_BAD_REQUEST = 400
    """
    The server cannot or will not process the request due to something that is perceived to be a client error 
    (e.g., malformed request syntax, invalid request message framing, or deceptive request routing)."""
    HTTP_401_UNAUTHENTICATED = 401
    """
    Although the HTTP standard specifies "unauthorized", semantically this response means "unauthenticated". 
    That is, the client must authenticate itself to get the requested response.
    """
    HTTP_403_FORBIDDEN = 403
    """
    The client does not have access rights to the content; that is, it is "unauthorized", so the server is refusing 
    to give the requested resource. Unlike 401 Unauthorized (which is technically UnAuthenticated);
    here, the client's identity is known to the server.
    """
    HTTP_404_NOT_FOUND = 404
    """
    The server cannot find the requested resource. In the browser, this means the URL is not recognized. 
    In an API, this can also mean that the endpoint is valid but the resource itself does not exist. 
    Servers may also send this response instead of 403 Forbidden to hide the existence of a resource from 
    an unauthorized client. This response code is probably the most well known due to its frequent occurrence on the web.
    """
    HTTP_405_METHOD_NOT_ALLOWED = 405
    """
    The request method is known by the server but is not supported by the target resource. 
    For example, an API may not allow calling DELETE to remove a resource.
    """
    HTTP_406_NOT_ACCEPTABLE = 406
    """
    This response is sent when the web server, after performing server-driven content negotiation, doesn't find any 
    content that conforms to the criteria given by the user agent.
    """
    HTTP_407_PROXY_AUTHENTICATION_REQUIRED = 407
    """
    This is similar to 401 Unauthorized but authentication is needed to be done by a proxy.
    """
    HTTP_408_REQUEST_TIMEOUT = 408
    """
    This response is sent on an idle connection by some servers, even without any previous request by the client. 
    It means that the server would like to shut down this unused connection. This response is used much more since 
    some browsers, like Chrome, Firefox 27+, or IE9, use HTTP pre-connection mechanisms to speed up surfing. 
    Also note that some servers merely shut down the connection without sending this message.
    """

    HTTP_415_UNSUPPORTED_MEDIA_TYPE = 415
    """
    The media format of the requested data is not supported by the server, so the server is rejecting the request.
    """

    HTTP_418_IM_A_TEAPOT = 418
    """
    The server refuses the attempt to brew coffee with a teapot.
    """

    HTTP_422_UNEXPECTED_OUTCOME = 422
    """
    The request was well-formed but was unable to be followed due to semantic errors.
    """

    HTTP_429_TOO_MANY_REQUESTS = 429
    """
    The user has sent too many requests in a given amount of time ("rate limiting").
    """

    HTTP_500_INTERNAL_SERVER_ERROR = 500
    """
    The server has encountered a situation it does not know how to handle.
    """
