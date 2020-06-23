# -*- coding: utf-8 -*-
#

from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.views import Response
from rest_framework_bulk import BulkModelViewSet

from common.permissions import IsSuperUserOrAppUser
from .models import Organization
from .serializers import OrgSerializer,  \
    OrgMembershipUserSerializer, OrgMembershipAdminSerializer, \
    OrgAllUserSerializer, OrgRetrieveSerializer, OrgReadSerializer
from users.models import User
from orgs.utils import current_org
from common.utils import get_logger
from .mixins.api import OrgMembershipModelViewSetMixin

logger = get_logger(__file__)


class OrgViewSet(BulkModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrgSerializer
    permission_classes = (IsSuperUserOrAppUser,)
    org = None

    def get_serializer_class(self):
        mapper = {
            'list': OrgReadSerializer,
            'retrieve': OrgRetrieveSerializer
        }
        return mapper.get(self.action, super().get_serializer_class())

    def get_data_from_model(self, model):
        if model == User:
            data = model.objects.filter(related_user_orgs__id=self.org.id)
        else:
            data = model.objects.filter(org_id=self.org.id)
        return data

    def destroy(self, request, *args, **kwargs):
        org = self.get_object()

        if str(current_org) == str(self.org):
            error = 'Could not delete current org'
            return Response({'error': error}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        if org.has_resouces:
            error = 'Current organization has resources, cannot be delete'
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        self.org.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrgMembershipAdminsViewSet(OrgMembershipModelViewSetMixin, BulkModelViewSet):
    serializer_class = OrgMembershipAdminSerializer
    # membership_class = Organization.admins.through
    permission_classes = (IsSuperUserOrAppUser, )


class OrgMembershipUsersViewSet(OrgMembershipModelViewSetMixin, BulkModelViewSet):
    serializer_class = OrgMembershipUserSerializer
    # membership_class = Organization.users.through
    permission_classes = (IsSuperUserOrAppUser, )


class OrgAllUserListApi(generics.ListAPIView):
    permission_classes = (IsSuperUserOrAppUser,)
    serializer_class = OrgAllUserSerializer
    filter_fields = ("username", "name")
    search_fields = filter_fields

    def get_queryset(self):
        pk = self.kwargs.get("pk")
        org = get_object_or_404(Organization, pk=pk)
        users = org.get_org_users().only(*self.serializer_class.Meta.only_fields)
        return users
