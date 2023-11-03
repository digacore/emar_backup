import re
from math import ceil

from flask_admin.base import expose
from flask_admin.contrib.sqla import ModelView, tools
from flask_admin._compat import string_types
from flask_login import current_user

from sqlalchemy.sql.expression import cast
from sqlalchemy import Unicode, or_
from sqlalchemy.orm.query import Query


class MyModelView(ModelView):
    """
    Custom ModelView class with view_permissions and custom search
    """

    page_size = 50

    def is_accessible(self):
        return current_user.is_authenticated

    def __repr__(self):
        return "MyModelView"

    def _available_companies(self, show_global: bool = False):
        """
        Returns query object with companies available for current user.
        This constructor should be used in the create and edit forms.

        Returns:
            query (Query): query object with companies available for current user
        """
        from app.models import Company, UserPermissionLevel

        match current_user.permission:
            case UserPermissionLevel.GLOBAL:
                if show_global:
                    available_companies: Query = Company.query.order_by(Company.name)
                else:
                    available_companies: Query = Company.query.filter(
                        Company.is_global.is_(False)
                    ).order_by(Company.name)
            case UserPermissionLevel.COMPANY:
                available_companies: Query = Company.query.filter_by(
                    id=current_user.company_id
                )
            case UserPermissionLevel.LOCATION_GROUP:
                available_companies: Query = Company.query.filter_by(
                    id=current_user.company_id
                )
            case UserPermissionLevel.LOCATION:
                available_companies: Query = Company.query.filter_by(
                    id=current_user.company_id
                )
            case _:
                available_companies: Query = Company.query.filter_by(id=-1)

        return available_companies

    def _available_locations(self):
        """
        Returns query object with locations available for current user.
        This constructor should be used in the create and edit forms.

        Returns:
            query (Query): query object with locations available for current user
        """
        from app.models import Location, UserPermissionLevel

        match current_user.permission:
            case UserPermissionLevel.GLOBAL:
                available_locations: Query = Location.query
            case UserPermissionLevel.COMPANY:
                available_locations: Query = Location.query.filter_by(
                    company_id=current_user.company_id
                )
            case UserPermissionLevel.LOCATION_GROUP:
                available_locations: Query = Location.query.filter(
                    Location.id.in_(
                        [loc.id for loc in current_user.location_group[0].locations]
                    )
                )
            case UserPermissionLevel.LOCATION:
                available_locations: Query = Location.query.filter_by(
                    id=current_user.location[0].id
                )
            case _:
                available_locations: Query = Location.query.filter_by(id=-1)

        return available_locations.order_by(Location.name)

    def _available_location_groups(self):
        """
        Returns query object with location groups available for current user.
        This constructor should be used in the create and edit forms.

        Returns:
            query (Query): query object with location groups available for current user
        """
        from app.models import LocationGroup, UserPermissionLevel

        match current_user.permission:
            case UserPermissionLevel.GLOBAL:
                available_groups: Query = LocationGroup.query
            case UserPermissionLevel.COMPANY:
                available_groups: Query = LocationGroup.query.filter_by(
                    company_id=current_user.company_id
                )
            case UserPermissionLevel.LOCATION_GROUP:
                available_groups: Query = LocationGroup.query.filter_by(
                    id=current_user.location_group[0].id
                )
            case _:
                available_groups: Query = LocationGroup.query.filter_by(id=-1)

        return available_groups.order_by(LocationGroup.name)

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
        column_name_match = re.search(r"\<\<(\w*)\>\>:", search)
        if column_name_match:
            column_name = column_name_match.group(1)
            # Create custom search field object on the base of column_name
            custom_search_field_obj = self.create_custom_search_field_obj(column_name)
            # Extract search value from search query
            search_value = re.search(r".*\>\>:(.*)", search).group(1)
        else:
            # Reinitialize search to update calculated field "status" of Computer
            if self.model.__tablename__ in ["computers"]:
                self.init_search()
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

    def _apply_filters(self, query, count_query, joins, count_joins, filters):
        # Refresh filters cache in case of Computer (for status field)
        if self.model.__tablename__ in ["computers"]:
            self._refresh_filters_cache()

        return super()._apply_filters(query, count_query, joins, count_joins, filters)

    # NOTE (danil): redefine this method to show in search "column_name: query"
    @expose("/")
    def index_view(self):
        """
        List view
        """
        from app.models import UserPermissionLevel

        if self.can_delete:
            delete_form = self.delete_form()
        else:
            delete_form = None

        # Grab parameters from URL
        view_args = self._get_list_extra_args()

        # Map column index to column name
        sort_column = self._get_column_by_idx(view_args.sort)
        if sort_column is not None:
            sort_column = sort_column[0]

        # Get page size
        page_size = view_args.page_size or self.page_size

        # Get count and data
        count, data = self.get_list(
            view_args.page,
            sort_column,
            view_args.sort_desc,
            view_args.search,
            view_args.filters,
            page_size=page_size,
        )

        list_forms = {}
        if self.column_editable_list:
            for row in data:
                list_forms[self.get_pk_value(row)] = self.list_form(obj=row)

        # Calculate number of pages
        if count is not None and page_size:
            num_pages = int(ceil(count / float(page_size)))
        elif not page_size:
            num_pages = 0  # hide pager for unlimited page_size
        else:
            num_pages = None  # use simple pager

        # Various URL generation helpers
        def pager_url(p):
            # Do not add page number if it is first page
            if p == 0:
                p = None

            return self._get_list_url(view_args.clone(page=p))

        def sort_url(column, invert=False, desc=None):
            if not desc and invert and not view_args.sort_desc:
                desc = 1

            return self._get_list_url(view_args.clone(sort=column, sort_desc=desc))

        def page_size_url(s):
            if not s:
                s = self.page_size

            return self._get_list_url(view_args.clone(page_size=s))

        # Actions
        actions, actions_confirmation = self.get_actions_list()
        if actions:
            action_form = self.action_form()
        else:
            action_form = None

        clear_search_url = self._get_list_url(
            view_args.clone(
                page=0,
                sort=view_args.sort,
                sort_desc=view_args.sort_desc,
                search=None,
                filters=None,
            )
        )

        # If user doesn't have global permission, hide company_name field (Computer, Location)
        list_of_columns = self._list_columns
        if current_user.permission != UserPermissionLevel.GLOBAL:
            list_of_columns = [
                column_obj
                for column_obj in list_of_columns
                if column_obj[0] != "company_name"
            ]

        # Search input value that would be displayed (if search arg present)
        search_input_value = None
        if view_args.search:
            search_column_name = re.search(r"\<\<(\w*)\>\>:", view_args.search)
            if search_column_name:
                search_column_name = " ".join(
                    [
                        word.capitalize()
                        for word in search_column_name.group(1).split("_")
                    ]
                ).replace("Pcc", "PointClickCare")
                search_query = re.search(r".*\>\>:(.*)", view_args.search).group(1)
                search_input_value = f"{search_column_name}: {search_query}"

        # Query params for /info/computers/ page
        url_with_all_params = self._get_list_url(view_args)
        params_for_computers_page = ""
        if "/admin/computer/" in url_with_all_params:
            params_for_computers_page = url_with_all_params.replace(
                "/admin/computer/", ""
            )
            params_for_computers_page = params_for_computers_page.replace(
                "search", "computers_search"
            ).replace("page", "computers_page")

        return self.render(
            self.list_template,
            data=data,
            list_forms=list_forms,
            delete_form=delete_form,
            action_form=action_form,
            # List
            list_columns=list_of_columns,
            sortable_columns=self._sortable_columns,
            editable_columns=self.column_editable_list,
            list_row_actions=self.get_list_row_actions(),
            # Pagination
            count=count,
            pager_url=pager_url,
            num_pages=num_pages,
            can_set_page_size=self.can_set_page_size,
            page_size_url=page_size_url,
            page=view_args.page,
            page_size=page_size,
            default_page_size=self.page_size,
            # Sorting
            sort_column=view_args.sort,
            sort_desc=view_args.sort_desc,
            sort_url=sort_url,
            # Search
            search_supported=self._search_supported,
            clear_search_url=clear_search_url,
            search=search_input_value if search_input_value else view_args.search,
            search_placeholder=self.search_placeholder(),
            # Filters
            filters=self._filters,
            filter_groups=self._get_filter_groups(),
            active_filters=view_args.filters,
            filter_args=self._get_filters(view_args.filters),
            # Actions
            actions=actions,
            actions_confirmation=actions_confirmation,
            # Misc
            enumerate=enumerate,
            get_pk_value=self.get_pk_value,
            get_value=self.get_list_value,
            return_url=self._get_list_url(view_args),
            # Extras
            extra_args=view_args.extra_args,
            params_for_computers_page=params_for_computers_page,
        )
