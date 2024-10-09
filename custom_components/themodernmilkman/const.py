"""Constants for the Modern Milkman integration."""

DOMAIN = "themodernmilkman"
TMM_LOGIN_URL = "https://tmm-website-xi.vercel.app/api/auth/login"
TMM_NEXT_DELIVERY_URL = "https://tmm-website-xi.vercel.app/api/delivery/next"
TMM_USER_WASTEAGE_URL = "https://tmm-website-xi.vercel.app/api/user/wastage"
TMM_USER_STATE_URL = "https://tmm-website-xi.vercel.app/api/user/state"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_CALENDARS = "calendars"
CONF_ACCESS_TOKEN = "access_token"
CONF_COOKIE_NAME = "__Secure-session"
CONF_CUSTOMER = "customer"
CONF_USER = "user"
CONF_FORENAME = "forename"
CONF_SURNAME = "surname"
CONF_BOTTLESSAVED = "bottlesSaved"
CONF_WASTAGE = "wastage"
CONF_NEXT_DELIVERY = "next_delivery"
CONF_DELIVERYDATE = "deliveryDate"
CONF_UNKNOWN = "Unknown"
REQUEST_HEADER = {
    "Content-Type": "application/json",
}
