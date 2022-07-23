import datetime as dt

from rest_framework import serializers

from djoser.serializers import UserSerializer

from .models import Achievement, AchievementCat, Cat, Owner, CHOICES

import webcolors


class Hex2NameColor(serializers.Field):
    # При чтении данных ничего не меняем - просто возвращаем как есть
    def to_representation(self, value):
        return value
    # При записи код цвета конвертируется в его название

    def to_internal_value(self, data):
        # Доверяй, но проверяй
        try:
            # Если имя цвета существует, то конвертируем код в название
            data = webcolors.hex_to_name(data)
        except ValueError:
            # Иначе возвращаем ошибку
            raise serializers.ValidationError('Для этого цвета нет имени')
        # Возвращаем данные в новом формате
        return data


class AchievementSerializer(serializers.ModelSerializer):
    achievement_name = serializers.CharField(source='name')

    class Meta:
        model = Achievement
        fields = ('id', 'achievement_name')


class CatListSerializer(serializers.ModelSerializer):
    color = serializers.ChoiceField(choices=CHOICES)

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color')


class CatSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(read_only=True)
    # Переопределяем поле achievements
    achievements = AchievementSerializer(many=True, required=False)
    age = serializers.SerializerMethodField()
    color = Hex2NameColor(choices=CHOICES)  # Вот он - наш собственный тип поля

    class Meta:
        model = Cat
        fields = ('id', 'name', 'color', 'birth_year',
                  'owner', 'achievements', 'age')

    def create(self, validated_data):
        # Если в исходном запросе не было поля achievements
        if 'achievements' not in self.initial_data:
            # То создаём запись о котике без его достижений
            cat = Cat.objects.create(**validated_data)
            return cat

    def get_age(self, obj):
        return dt.datetime.now().year - obj.birth_year

        # Иначе делаем следующее:
        # Уберём список достижений из словаря validated_data и сохраним его
        achievements = validated_data.pop('achievements')
        # Сначала добавляем котика в БД
        cat = Cat.objects.create(**validated_data)
        # А потом добавляем его достижения в БД
        for achievement in achievements:
            current_achievement, status = Achievement.objects.get_or_create(
                **achievement)
            # И связываем каждое достижение с этим котиком
            AchievementCat.objects.create(
                achievement=current_achievement, cat=cat)
        return cat


class OwnerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Owner
        fields = ('first_name', 'last_name', 'cats')


class CustomUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name')
