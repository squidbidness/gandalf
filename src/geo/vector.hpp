#ifndef VECTOR_HPP_DA39A3EE
#define VECTOR_HPP_DA39A3EE

#include <boost/hana/integral_constant.hpp>
#include <boost/hana/fold_left.hpp>
#include <boost/hana/range.hpp>

#include <algorithm>
#include <array>
#include <initializer_list>


namespace geo::vector_implementation {

	using namespace boost::hana::literals;
	namespace hana = boost::hana;

	template< typename T, size_t N, size_t I >
	struct VectorBase;

	template< typename T, size_t N >
	struct VectorBase< T, N, 0 > : std::array<T, N> {

		using Base = std::array<T, N>;

		using Base::operator [];

		template< int I >
		constexpr T &operator[](
				std::integral_constant< int, I >
				)
		{
			return std::get<I>( *this );
		}
		template< int I >
		constexpr T const &operator[](
				std::integral_constant< int, I > i_c
				) const
		{
			return std::get<I>( *this );
		}
	};

	template< typename T, size_t N>
	struct VectorBase< T, N, 1 > : VectorBase<T, N, 0> {
		T &x() { return (*this)[0_c]; }
		T const &x() const { return (*this)[0_c]; }
	};

	template< typename T, size_t N >
	struct VectorBase< T, N, 2 > : VectorBase<T, N, 1> {
		T &y() { return (*this)[1_c]; }
		T const &y() const { return (*this)[1_c]; }
	};

	template< typename T, size_t N >
	struct VectorBase< T, N, 3 > : VectorBase<T, N, 2> {
		T &z() { return (*this)[2_c]; }
		T const &z() const { return (*this)[2_c]; }
	};

	template< typename T, size_t N >
	struct VectorBase< T, N, 4 > : VectorBase<T, N, 3> {
		T &w() { return (*this)[3_c]; }
		T const &w() const { return (*this)[3_c]; }
	};

	template< typename T, size_t N, size_t I >
	struct VectorBase : VectorBase<T, N, I-1>
	{ };


	template< typename T, size_t N >
	using Vector = VectorBase<T, N, N>;

}

namespace std {
	template< typename T, size_t N >
	struct tuple_size< geo::vector_implementation::Vector<T, N> >
			: tuple_size< array<T, N> >
	{ };
}

namespace geo::vector_implementation::interface {

	using geo::vector_implementation::Vector;

	template< typename Vec >
	concept bool Vector_CV
			= requires() {
				typename std::remove_reference_t<Vec>::value_type;
				std::tuple_size<std::remove_reference_t<Vec>>::value;
			}
			&& std::is_same_v<
					Vector<
						typename std::remove_reference_t<Vec>::value_type,
						std::tuple_size<std::remove_reference_t<Vec>>::value
						>,
					std::remove_reference_t<Vec>
					>;

	template< typename Vec, typename ...Vecs >
	concept bool VectorsOfSameSize_CV
			= ( Vector_CV<Vec> && ... && Vector_CV<Vecs> )
			&& (( std::tuple_size<std::remove_reference_t<Vec>>::value
				== std::tuple_size<std::remove_reference_t<Vecs>>::value ) && ...);


	template< typename A, typename B, typename C >
	struct ComponentOpResultAllVoid : std::bool_constant<false>
	{ };

	template< typename ComponentOp, typename ...Vecs, int ...Is >
	struct ComponentOpResultAllVoid<ComponentOp, std::tuple<Vecs...>, std::integer_sequence<int, Is...>>
			: std::bool_constant<
				requires( ComponentOp op, Vecs ...vecs, std::integral_constant<int, Is> ...is ) {
					requires (std::is_same_v<void, decltype(op(is, vecs...))> && ...);
				} >
	{ };

	template< typename A, typename B, typename C >
	static constexpr bool ComponentOpResultAllVoid_v = ComponentOpResultAllVoid<A, B, C>::value;


	template< typename A, typename B, typename C >
	struct ComponentOpResultAllNonVoid : std::bool_constant<false>
	{ };

	template< typename ComponentOp, typename ...Vecs, int ...Is >
	struct ComponentOpResultAllNonVoid<ComponentOp, std::tuple<Vecs...>, std::integer_sequence<int, Is...>>
			: std::bool_constant<
				requires( ComponentOp op, Vecs ...vecs, std::integral_constant<int, Is> ...is ) {
					requires ( (!std::is_same_v<void, decltype(op(is, vecs...))>) && ... );
				} >
	{ };

	template< typename A, typename B, typename C >
	static constexpr bool ComponentOpResultAllNonVoid_v = ComponentOpResultAllNonVoid<A, B, C>::value;


	template< typename ComponentOp, typename Vecs, typename Is >
	concept bool ComponentOpConsistentResult_CV
			= ComponentOpResultAllVoid_v<ComponentOp, Vecs, Is>
			|| ComponentOpResultAllNonVoid_v<ComponentOp, Vecs, Is>;


	template< typename ...T >
	constexpr auto makeVector( T &&...t ) {
		return Vector< std::common_type_t<T...>, sizeof...(T) >{
				std::forward<T>( t )... };
	}

	namespace Vector_shorthand {
		constexpr auto V_( auto &&...t ) {
			return makeVector( std::forward<decltype(t)>( t )... );
		};
	}


	template< typename ComponentOp, typename ...Vecs, int ...Is >
	// requires ComponentOpConsistentResult_CV<ComponentOp, Vecs..., Is...>
	constexpr auto forEachComponentHelper(
			ComponentOp &&op,
			std::integer_sequence<int, Is...>,
			Vecs &&...vecs
			)
	{
		if constexpr ( ComponentOpResultAllVoid_v<ComponentOp, std::tuple<Vecs...>, std::integer_sequence<int, Is...>> ) {
			( op( hana::int_c<Is>, std::forward<Vecs>(vecs)... ), ... );
		} else {
			return makeVector( op( hana::int_c<Is>, std::forward<Vecs>(vecs)... )... );
		}
	}

	template< typename ComponentOp, typename Vec, typename ...Vecs >
	requires VectorsOfSameSize_CV<Vec, Vecs...>
	constexpr auto forEachComponent(
			ComponentOp &&op,
			Vec &&vec,
			Vecs &&...vecs
			)
	{
		return forEachComponentHelper(
				std::forward<ComponentOp>( op ),
				std::make_integer_sequence<int, std::tuple_size<std::remove_reference_t<Vec>>::value>(),
				std::forward< Vec >( vec ),
				std::forward< Vecs >( vecs )...
				);
	}


	template< typename T, typename S, size_t N >
	constexpr auto dot( Vector<T, N> const &a, Vector<S, N> const &b ) {

		using Sum = decltype( std::declval<T>() + std::declval<S>() );
		using hana::fold_left;
		return fold_left(
				hana::make_range( 0_c, hana::int_c<N> ),
				Sum(0),
				[&] ( Sum sum, auto i ) {
					return sum + a[i] * b[i];
				}
				);
	}


	template< typename T, typename S >
	constexpr auto cross( Vector<T, 3> const &a, Vector<S, 3> const &b ) {
		using namespace Vector_shorthand;
		return V_( a.y() * b.z() - a.z() * b.y(),
				a.z() * b.x() - a.x() * b.z(),
				a.x() * b.y() - a.y() * b.x() );
	}


	template< size_t N > using VectorF = Vector<float, N>;
	template< size_t N > using VectorD = Vector<double, N>;

	template< typename T > using Vector1 = Vector<T, 1>;
	template< typename T > using Vector2 = Vector<T, 2>;
	template< typename T > using Vector3 = Vector<T, 3>;
	template< typename T > using Vector4 = Vector<T, 4>;

	using VectorF1 = VectorF<1>;
	using VectorF2 = VectorF<2>;
	using VectorF3 = VectorF<3>;
	using VectorF4 = VectorF<4>;

	using VectorD1 = VectorD<1>;
	using VectorD2 = VectorD<2>;
	using VectorD3 = VectorD<3>;
	using VectorD4 = VectorD<4>;

}

namespace geo {
	using namespace vector_implementation::interface;
}

#endif
