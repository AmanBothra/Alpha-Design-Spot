from model_utils.models import TimeStampedModel


class BaseModel(TimeStampedModel):
    class Meta:
        abstract = True

    @property
    def added_on(self):
        return self.created

    @property
    def updated_on(self):
        return self.modified

    def save(self, *args, **kwargs):
        if self.pk and 'update_fields' not in kwargs:
            # Only check changed fields if not explicitly provided
            cls = self.__class__
            try:
                # Only fetch fields that can be compared (exclude relations and computed fields)
                comparable_fields = [
                    f.name for f in cls._meta.get_fields() 
                    if not f.many_to_many and not f.one_to_many and hasattr(f, 'attname')
                ]
                old = cls.objects.only('id', *comparable_fields).get(pk=self.pk)
                
                changed_fields = []
                for field_name in comparable_fields:
                    try:
                        old_value = getattr(old, field_name, None)
                        new_value = getattr(self, field_name, None)
                        if old_value != new_value:
                            changed_fields.append(field_name)
                    except (AttributeError, ValueError):
                        # Skip fields that can't be compared
                        continue
                
                if changed_fields:
                    kwargs['update_fields'] = changed_fields
                else:
                    # No changes detected, skip save
                    return
            except cls.DoesNotExist:
                # Object doesn't exist in DB yet, proceed with normal save
                pass
        super().save(*args, **kwargs)
