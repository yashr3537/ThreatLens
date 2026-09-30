#include "json.h"

std::string json_escape(const std::string& value)
{
	static const char hex[] = "0123456789abcdef";
	std::string escaped;

	for (unsigned char character : value)
	{
		switch (character)
		{
		case '"': escaped += "\\\""; break;
		case '\\': escaped += "\\\\"; break;
		case '\b': escaped += "\\b"; break;
		case '\f': escaped += "\\f"; break;
		case '\n': escaped += "\\n"; break;
		case '\r': escaped += "\\r"; break;
		case '\t': escaped += "\\t"; break;
		default:
			if (character < 0x20)
			{
				escaped += "\\u00";
				escaped += hex[(character >> 4) & 0x0f];
				escaped += hex[character & 0x0f];
			}
			else
			{
				escaped += static_cast<char>(character);
			}
		}
	}

	return escaped;
}

std::string json_quote(const std::string& value)
{
	return "\"" + json_escape(value) + "\"";
}