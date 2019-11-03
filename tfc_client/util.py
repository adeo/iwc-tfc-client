import inflection


class InflectionStr(str):
    def __getattr__(self, name):
        if hasattr(inflection, name):
            inflection_method = getattr(inflection, name)
            if callable(inflection_method):
                return InflectionStr(inflection_method(self))
        else:
            raise AttributeError(name)
        # return super().__getattr__(name)


if __name__ == "__main__":
    test = InflectionStr("people")
    print(test.camelize.singularize)
