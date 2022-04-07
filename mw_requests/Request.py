import requests
from .Errors import FieldNotFoundError
import json

class Request():
    def __init__(self, request, add_headers={}, add_payload={}, add_query={}):
        """
        Request for Marketwatch automation

        :param request: request as json loaded dict
        :param add_headers: required additional headers
        :param add_payload: required additional payload
        :param add_query: required additional query params
        """
        self.url = request["url"]
        self.method = request.get("method", "GET")
        self.form_encoded = request.get("form_encoded", False)
        self.payload_is_list = request.get("payload_is_list", False)

        self.headers = self.add_fields(
            request.get("headers", {}),
            request.get("required_headers", []),
            add_headers,
            "Headers"
        )
        self.payload = self.add_fields(
            request.get("payload", {}),
            request.get("required_payload", []),
            add_payload,
            "Payload"
        )
        self.query = self.add_fields(
            request.get("query", {}),
            request.get("required_query", []),
            add_query,
            "Query"
        )

    def add_fields(self, request_param, required_field_labels, field_values, name):
        """
        Add required fields to request param

        :param request_param: dict of default request param
        :param required_field_labels: required added fields
        :param field_values: values of required added fields
        :param name: name of request param:
        :returns: modified request param dict
        """
        for field in required_field_labels:
            try:
                request_param[field] = field_values.pop(field)
            except KeyError:
                raise FieldNotFoundError(f"{name} {field} is required")
        
        return request_param

    def send_request(self, session, verbose=False):
        """
        Prepare and send request

        :param session: session object to send request
        :param verbose: run function verbose
        :returns: response object
        """
        request = requests.Request(self.method, self.url)

        # Add headers
        if len(self.headers) > 0:
            request.headers = self.headers
        request.headers["cookie"] = self.dict_to_cookies(session.cookies.get_dict())
        # Add payload
        if len(self.payload) > 0:
            request.data = self.get_payload_as_string()
        # Add query params
        request.params = self.query
        
        if verbose:
            print(self.url)
            print(f"Cookies: {session.cookies.get_dict()}")
            print(f"Headers: {request.headers}")
            print(f"Payload: {request.data}")
            print()

        request = request.prepare()
        return session.send(request)

    def get_payload_as_string(self):
        """
        Get request payload as string

        :returns: payload as string
        """
        # Check if payload is form encoded
        if self.form_encoded:
            return self.payload
        else:
            # Check if payload is list
            if self.payload_is_list:
                return json.dumps([self.payload])
            else:
                return json.dumps(self.payload)

    def dict_to_cookies(self, cookie_dict):
        """
        Convert dict to cookie string

        :param cookie_dict: dictionary of cookies
        :returns: cookies as semicolon delimited string
        """
        return "; ".join([f"{key}={cookie_dict[key]}" for key in cookie_dict])
