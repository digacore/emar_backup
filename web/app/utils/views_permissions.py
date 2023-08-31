import re

from flask_admin.contrib.sqla import ModelView, tools
from flask_admin._compat import string_types
from flask_login import current_user

from sqlalchemy.sql.expression import cast
from sqlalchemy import Unicode, or_


class MyModelView(ModelView):
    """
    Custom ModelView class with view_permissions and custom search
    """

    page_size = 50

    def is_accessible(self):
        return current_user.is_authenticated

    def __repr__(self):
        return "MyModelView"

    def create_custom_search_field_obj(self, column_name):
        """Create custom search field object"""
        custom_search_field_obj = []
        attr, joins = tools.get_field_with_path(self.model, column_name)

        if not attr:
            raise Exception("Failed to find field for search field: %s" % column_name)

        if tools.is_hybrid_property(self.model, column_name):
            column = attr
            if isinstance(column_name, string_types):
                column.key = column_name.split(".")[-1]
            custom_search_field_obj.append((column, joins))
        else:
            for column in tools.get_columns_for_field(attr):
                custom_search_field_obj.append((column, joins))

        return custom_search_field_obj

    # NOTE(danil): despite the fact that this is protected method, I have to redefine it
    # to make it possible to search by every table column separately
    def _apply_search(self, query, count_query, joins, count_joins, search):
        """
        Apply search to a query.
        """
        # Extract column_name from search query
        column_name_match = re.search(r"\<\<\<(\w*)\>\>\>", search)
        if column_name_match:
            column_name = column_name_match.group(1)
            # Create custom search field object on the base of column_name
            custom_search_field_obj = self.create_custom_search_field_obj(column_name)
            # Extract search value from search query
            search_value = re.search(r".*\>\>\>(.*)", search).group(1)
        else:
            custom_search_field_obj = None
            search_value = search

        terms = search_value.split(" ")

        fields_for_search = (
            custom_search_field_obj if custom_search_field_obj else self._search_fields
        )

        for term in terms:
            if not term:
                continue

            stmt = tools.parse_like_term(term)

            filter_stmt = []
            count_filter_stmt = []

            for field, path in fields_for_search:
                query, joins, alias = self._apply_path_joins(
                    query, joins, path, inner_join=False
                )

                count_alias = None

                if count_query is not None:
                    count_query, count_joins, count_alias = self._apply_path_joins(
                        count_query, count_joins, path, inner_join=False
                    )

                column = field if alias is None else getattr(alias, field.key)
                filter_stmt.append(cast(column, Unicode).ilike(stmt))

                if count_filter_stmt is not None:
                    column = (
                        field
                        if count_alias is None
                        else getattr(count_alias, field.key)
                    )
                    count_filter_stmt.append(cast(column, Unicode).ilike(stmt))

            query = query.filter(or_(*filter_stmt))

            if count_query is not None:
                count_query = count_query.filter(or_(*count_filter_stmt))

        return query, count_query, joins, count_joins
